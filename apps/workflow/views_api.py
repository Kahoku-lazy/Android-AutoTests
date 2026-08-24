"""workflow DRF ViewSets — directory + document CRUD, import/export, move."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import api as wf_api
from .models import WorkflowDirectory, WorkflowDocument
from .serializers import (
    WorkflowDirectorySerializer,
    WorkflowDocumentDetailSerializer,
    WorkflowDocumentListSerializer,
)


class WorkflowDirectoryViewSet(viewsets.ModelViewSet):
    """目录 CRUD — list 同时返回 flat + tree，move 为 @action."""

    queryset = WorkflowDirectory.objects.order_by("sort_order", "id")
    serializer_class = WorkflowDirectorySerializer

    def list(self, request, *args, **kwargs):
        """GET /directories/ — 同时返回 flat 列表和递归 tree."""
        flat = wf_api.list_directories_flat()
        tree = wf_api.get_directory_tree()
        return Response(
            {
                "directories": flat,
                "tree": tree,
            }
        )

    def perform_create(self, serializer):
        """POST /directories/ — 委托 api.py 校验（同名冲突等）."""
        data = serializer.validated_data
        ok, result = wf_api.create_directory(
            name=data["name"],
            parent_id=data.get("parent_id"),
            sort_order=data.get("sort_order", 0),
        )
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"name": result})
        serializer.instance = WorkflowDirectory.objects.get(id=result["id"])

    def perform_update(self, serializer):
        """PUT/PATCH /directories/{id}/ — 委托 api.py."""
        data = serializer.validated_data
        parent_id = data.pop("parent_id", None) if "parent_id" in data else None
        # save() handles name/sort_order via serializer
        instance = serializer.save()
        if parent_id is not None:
            ok, result = wf_api.update_directory(
                instance.id,
                name=data.get("name"),
                parent_id=parent_id,
            )
            if not ok:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"parent_id": result})

    def perform_destroy(self, instance):
        """DELETE /directories/{id}/ — 级联删除子目录内文档."""
        wf_api.delete_directory(instance.id)

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """POST /directories/{id}/move/ — 移动目录."""
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
        qs = WorkflowDocument.objects.filter(doc_type=WorkflowDocument.TYPE_PAGE_FLOW).order_by(
            "-updated_at"
        )
        directory_id = self.request.query_params.get("directory_id")
        doc_type = self.request.query_params.get("doc_type")
        if directory_id and directory_id.isdigit():
            qs = qs.filter(directory_id=int(directory_id))
        if doc_type == WorkflowDocument.TYPE_TEST_CASE:
            return qs.none()
        if doc_type and doc_type != WorkflowDocument.TYPE_PAGE_FLOW:
            return qs.none()
        return qs

    def perform_create(self, serializer):
        """POST /documents/ — 委托 api.py upsert（自动生成 doc_id）."""
        data = serializer.validated_data
        ok, result, status = wf_api.upsert_document(
            doc_id=None,
            title=data["title"],
            doc_type=data["doc_type"],
            config=data.get("config_json", {}),
            directory_id=data.get("directory_id"),
            description=data.get("description", ""),
        )
        if not ok:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": result})
        serializer.instance = WorkflowDocument.objects.get(doc_id=result["doc_id"])

    def perform_update(self, serializer):
        """PUT/PATCH /documents/{doc_id}/ — upsert by doc_id."""
        data = serializer.validated_data
        doc_id = self.kwargs["doc_id"]
        ok, result, status = wf_api.upsert_document(
            doc_id=doc_id,
            title=data.get("title"),
            doc_type=data.get("doc_type"),
            config=data.get("config_json", {}),
            directory_id=data.get("directory_id"),
            description=data.get("description", ""),
            allow_create=False,
        )
        if not ok:
            if status == 404:
                from rest_framework.exceptions import NotFound

                raise NotFound(detail=result)
            from rest_framework.exceptions import ValidationError

            raise ValidationError(detail=result)
        serializer.instance = WorkflowDocument.objects.get(doc_id=doc_id)

    def perform_destroy(self, instance):
        """DELETE /documents/{doc_id}/ — 委托 api.py."""
        wf_api.delete_document(instance.doc_id)

    @action(detail=False, methods=["post"])
    def _import(self, request):
        """POST /documents/import/ — 导入 envelope JSON."""
        overwrite = request.query_params.get("overwrite") in ("1", "true", "True")
        payload = (
            request.data.get("envelope")
            if isinstance(request.data.get("envelope"), dict)
            else request.data
        )
        ok, result, status = wf_api.import_document_envelope(payload, overwrite=overwrite)
        if not ok:
            return Response({"message": result}, status=status)
        return Response(result)

    @action(detail=True, methods=["get"])
    def export(self, request, doc_id=None):
        """GET /documents/{doc_id}/export/ — 导出为 envelope JSON."""
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
        """POST /documents/{doc_id}/move/ — 移动文档到目录."""
        raw = request.data.get("directory_id", request.data.get("parent_id"))
        dir_id = None if raw in (None, "", "null") else int(raw)
        ok, result = wf_api.move_document(doc_id, dir_id)
        if not ok:
            return Response({"message": result}, status=400)
        return Response(result)
