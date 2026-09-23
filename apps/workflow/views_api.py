"""workflow DRF ViewSets — prototype + directory + document CRUD."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from . import api as wf_api
from .models import WorkflowDirectory, WorkflowDocument, WorkflowPrototype
from .serializers import (
    WorkflowDirectorySerializer,
    WorkflowDocumentDetailSerializer,
    WorkflowDocumentListSerializer,
    WorkflowPrototypeSerializer,
)


def _q_prototype_id(request) -> int | None:
    raw = request.query_params.get("prototype_id")
    if raw in (None, "", "null"):
        return None
    if str(raw).isdigit():
        return int(raw)
    return None


def _directory_id_from(value) -> int | None:
    """把请求里的 directory_id 归一为 int | None（null / 空串 → None，即原型根）."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"directory_id": "必须是整数或 null"})


class WorkflowPrototypeViewSet(ViewSet):
    """原型 CRUD — 标准信封由 EnvelopeJSONRenderer 包裹."""

    # 仅作 schema 元数据：本 ViewSet 直接调 wf_api，不经 get_queryset / get_serializer。
    # 声明后 drf-spectacular 才能推导 {id} 路径参数类型与原型响应结构，消除告警。
    serializer_class = WorkflowPrototypeSerializer
    queryset = WorkflowPrototype.objects.none()
    # 主键只允许数字：字面量段（如历史的 `create/`）不再被详情路由当主键吃掉，
    # 既让下线后的旧地址返回 404 而不是 405/500，也避免非数字主键触发 ValueError。
    lookup_value_regex = r"\d+"

    def list(self, request):
        return Response(wf_api.list_prototypes())

    def create(self, request):
        ok, result, status = wf_api.create_prototype(
            name=request.data.get("name", ""),
            description=request.data.get("description") or "",
        )
        if not ok:
            return Response({"message": result}, status=status)
        return Response(result, status=status)

    def retrieve(self, request, pk=None):
        proto = wf_api.get_prototype(int(pk))
        if not proto:
            return Response({"message": "原型不存在"}, status=404)
        return Response(proto)

    def partial_update(self, request, pk=None):
        ok, result, status = wf_api.update_prototype(
            int(pk),
            name=request.data.get("name"),
            description=request.data.get("description"),
        )
        if not ok:
            return Response({"message": result}, status=status)
        return Response(result)

    def update(self, request, pk=None):
        return self.partial_update(request, pk=pk)

    def destroy(self, request, pk=None):
        ok, result, status = wf_api.delete_prototype(int(pk))
        if not ok:
            return Response({"message": result}, status=status)
        return Response({"id": int(pk)})


class WorkflowDirectoryViewSet(viewsets.ModelViewSet):
    """目录 CRUD — list 同时返回 flat + tree，move 为 @action."""

    queryset = WorkflowDirectory.objects.order_by("sort_order", "id")
    serializer_class = WorkflowDirectorySerializer
    # 同 WorkflowPrototypeViewSet：主键只允许数字，字面量段不再被详情路由吃掉。
    lookup_value_regex = r"\d+"

    def list(self, request, *args, **kwargs):
        proto_id = _q_prototype_id(request)
        flat = wf_api.list_directories_flat(prototype_id=proto_id)
        tree = wf_api.get_directory_tree(prototype_id=proto_id)
        return Response({"directories": flat, "tree": tree})

    def perform_create(self, serializer):
        data = serializer.validated_data
        ok, result = wf_api.create_directory(
            name=data["name"],
            parent_id=data.get("parent_id"),
            sort_order=data.get("sort_order", 0),
            prototype_id=self.request.data.get("prototype_id"),
        )
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"name": result})
        serializer.instance = WorkflowDirectory.objects.get(id=result["id"])

    def perform_update(self, serializer):
        data = serializer.validated_data
        instance = serializer.instance
        # 显式 parent_id=null 表示「移到根」；api 约定用空串表达（api 内 "" → parent=None）
        parent_id = data.get("parent_id") if "parent_id" in data else None
        if parent_id is None and "parent_id" in data:
            parent_id = ""
        # 单一写路径：校验全在 api 内完成，失败时不产生任何写入
        ok, result = wf_api.update_directory(
            instance.id,
            name=data.get("name"),
            parent_id=parent_id,
            sort_order=data.get("sort_order"),
        )
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": result})
        serializer.instance = WorkflowDirectory.objects.get(id=instance.id)

    def perform_destroy(self, instance):
        ok, result = wf_api.delete_directory(instance.id)
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": result})

    def destroy(self, request, *args, **kwargs):
        """返回 200 + 空 data，走信封 {status:true}；避免默认 204 空体让前端判失败。"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({})

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        dir_id = self.get_object().id
        parent_id = request.data.get("parent_id")
        if parent_id not in (None, "", "null"):
            parent_id = int(parent_id)
        else:
            parent_id = None
        ok, result = wf_api.move_directory(dir_id, parent_id)
        if not ok:
            return Response({"message": result}, status=400)
        return Response(result)


class WorkflowDocumentViewSet(viewsets.ModelViewSet):
    """文档 CRUD — doc_id 为 natural key，支持 import/export/move."""

    lookup_field = "doc_id"
    lookup_value_regex = r"[-\w]+"

    def get_serializer_class(self):
        if self.action in ("list",):
            return WorkflowDocumentListSerializer
        return WorkflowDocumentDetailSerializer

    def get_queryset(self):
        qs = WorkflowDocument.objects.filter(
            doc_type__in=WorkflowDocument.SUPPORTED_TYPES
        ).order_by("-updated_at")
        proto_id = _q_prototype_id(self.request)
        if proto_id is not None:
            qs = qs.filter(prototype_id=proto_id)
        directory_id = self.request.query_params.get("directory_id")
        doc_type = self.request.query_params.get("doc_type")
        if directory_id and directory_id.isdigit():
            qs = qs.filter(directory_id=int(directory_id))
        if doc_type:
            if doc_type not in WorkflowDocument.SUPPORTED_TYPES:
                return qs.none()
            qs = qs.filter(doc_type=doc_type)
        return qs

    def perform_create(self, serializer):
        raw = self.request.data
        ok, result, status = wf_api.upsert_document(
            doc_id=None,
            title=raw.get("title") or raw.get("name") or "",
            doc_type=raw.get("doc_type") or "",
            config=raw.get("config") if raw.get("config") is not None else {},
            directory_id=_directory_id_from(raw.get("directory_id")),
            description=raw.get("description") or "",
            prototype_id=raw.get("prototype_id"),
        )
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": result})
        serializer.instance = WorkflowDocument.objects.get(doc_id=result["doc_id"])

    def perform_update(self, serializer):
        """按提交字段合并：没提交的字段保持原值（与 legacy PUT 语义一致）。

        不能用 `validated_data.get(字段, 空值)` 判断"没提交"——`validated_data` 不含未提交
        字段，`get(..., 默认值)` 会把"没提交"读成"提交了空值"，曾造成「只改标题被 400」
        与「保存时描述被清空」。故以 `request.data` 的键存在性为准。
        """
        raw = self.request.data
        doc_id = self.kwargs["doc_id"]
        existing = wf_api.get_document(doc_id)
        if not existing:
            from rest_framework.exceptions import NotFound

            raise NotFound(detail="文档不存在")

        if "directory_id" in raw:
            directory_id = _directory_id_from(raw.get("directory_id"))
            clear_directory = directory_id is None
        else:
            directory_id = existing.get("directory_id")
            clear_directory = False

        ok, result, status = wf_api.upsert_document(
            doc_id=doc_id,
            title=raw.get("title") or existing["title"],
            doc_type=raw.get("doc_type") or existing["doc_type"],
            config=raw["config"] if "config" in raw else existing["config"],
            directory_id=directory_id,
            description=raw.get("description", existing.get("description") or ""),
            allow_create=False,
            clear_directory=clear_directory,
            prototype_id=existing.get("prototype_id"),
        )
        if not ok:
            if status == 404:
                from rest_framework.exceptions import NotFound

                raise NotFound(detail=result)
            from rest_framework.exceptions import ValidationError

            raise ValidationError(detail=result)
        serializer.instance = WorkflowDocument.objects.get(doc_id=doc_id)

    def perform_destroy(self, instance):
        wf_api.delete_document(instance.doc_id)

    def destroy(self, request, *args, **kwargs):
        """返回 200 + 空 data，走信封 {status:true}；避免默认 204 空体让前端判失败。"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({})

    @action(detail=False, methods=["post"], url_path="import")
    def _import(self, request):
        """POST /api/workflow/documents/import — 导入 envelope；?overwrite=1 覆盖同 doc_id."""
        overwrite = request.query_params.get("overwrite") in ("1", "true", "True")
        payload = (
            request.data.get("envelope")
            if isinstance(request.data.get("envelope"), dict)
            else request.data
        )
        if isinstance(payload, dict) and not payload.get("prototype_id"):
            pid = request.data.get("prototype_id") or _q_prototype_id(request)
            if pid is not None:
                payload = {**payload, "prototype_id": pid}
        ok, result, status = wf_api.import_document_envelope(payload, overwrite=overwrite)
        if not ok:
            return Response({"message": result}, status=status)
        return Response(result)

    @action(detail=True, methods=["get"])
    def export(self, request, doc_id=None):
        download = request.query_params.get("download") in ("1", "true", "True")
        ok, result = wf_api.export_document(doc_id)
        if not ok:
            return Response({"message": result}, status=404)
        if download:
            import json

            from django.http import HttpResponse

            body = json.dumps(result, ensure_ascii=False, indent=2)
            resp = HttpResponse(body, content_type="application/json; charset=utf-8")
            resp["Content-Disposition"] = f'attachment; filename="{doc_id}.json"'
            return resp
        return Response({"envelope": result})

    @action(detail=True, methods=["post"])
    def move(self, request, doc_id=None):
        raw = request.data.get("directory_id", request.data.get("parent_id"))
        dir_id = None if raw in (None, "", "null") else int(raw)
        ok, result = wf_api.move_document(doc_id, dir_id)
        if not ok:
            return Response({"message": result}, status=400)
        return Response(result)
