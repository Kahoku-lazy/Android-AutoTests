"""case_manager DRF ViewSets — 4 case types + directories + shared lock/unlock/visibility.

All case ViewSets inherit from ``BaseCaseViewSet`` which handles:
  - Visibility filtering (public + creator + restricted with permitted_users)
  - Directory sub-tree expansion
  - Optimistic lock checking
  - User field assignment (created_by / updated_by)
"""

import json

from datetime import datetime
from typing import ClassVar

from django.db import models as db_models
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from . import api_directories
from .api_api import save_api_definition
from .api_lock import (
    acquire_edit_lock,
    delete_case,
    release_edit_lock,
    set_case_lock,
    set_case_visibility,
)
from .api_storage import save_storage_definition
from .api_ui import ConflictError, save_definition
from .api_web import save_web_definition
from .models import CaseDirectory, TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase
from .serializers import (
    ApiTestCaseSerializer,
    CaseDirectorySerializer,
    StorageTestCaseSerializer,
    TestDefinitionSerializer,
    WebTestCaseSerializer,
)

# Model → save_* 分派映射（写操作收敛到 api 层单一写源）
_SAVE_FN = {
    TestDefinition: save_definition,
    ApiTestCase: save_api_definition,
    StorageTestCase: save_storage_definition,
    WebTestCase: save_web_definition,
}

# ── Helpers ──


def _user_id(request):
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return str(uid)
    user = getattr(request, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)
    return ""


def _make_id(prefix: str) -> str:
    import random
    import string

    now = datetime.now()
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"


def _raise_lock_error(result):
    """将 api_lock 的 error_dict 转为 DRF 异常。"""
    code = result.get("code", 400)
    message = result.get("message", "操作失败")
    if code == 404:
        raise NotFound(message)
    if code == 400:
        raise ValidationError({"detail": message})
    raise PermissionDenied(message)


# ═══════════════════════════════════════════════════════
# Base Case ViewSet
# ═══════════════════════════════════════════════════════


class BaseCaseViewSet(viewsets.ModelViewSet):
    """Shared base for all case-type ViewSets."""

    model: ClassVar[type[db_models.Model] | None] = None
    id_prefix = ""

    def get_model(self):
        return self.model

    def get_queryset(self):
        model = self.get_model()
        qs = model.objects.select_related("directory").order_by("-updated_at")
        user = _user_id(self.request)

        qs = qs.filter(
            db_models.Q(visibility="public")
            | db_models.Q(visibility="hidden", created_by=user)
            | db_models.Q(visibility="restricted", permitted_users__contains=f'"{user}"')
        )

        directory_id = self.request.query_params.get("directory_id")
        if directory_id and directory_id.isdigit():
            dir_id = int(directory_id)
            sub_ids = [dir_id]
            for child in CaseDirectory.objects.filter(parent_id=dir_id):
                sub_ids.append(child.id)
            qs = qs.filter(directory_id__in=sub_ids)

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)

        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        return qs

    def perform_create(self, serializer):
        model = self.get_model()
        user = _user_id(self.request)
        data = dict(serializer.validated_data)

        new_id = _make_id(self.id_prefix)

        # directory 对象 → directory_id；steps_data_write → steps_data（save_* 统一处理）
        directory = data.pop("directory", None)
        if directory is not None:
            data["directory_id"] = directory.id
        if "steps_data_write" in data:
            data["steps_data"] = data.pop("steps_data_write")
        data["created_by"] = user
        data["updated_by"] = user

        try:
            instance = _SAVE_FN[model](new_id, **data)
        except (ConflictError, ValueError) as e:
            raise ValidationError({"detail": str(e)})

        serializer.instance = instance

    def perform_update(self, serializer):
        instance = self.get_object()
        user = _user_id(self.request)
        data = serializer.validated_data

        # Check duplicate title
        directory = data.get("directory", instance.directory)
        new_title = data.get("title", instance.title)
        if directory and new_title != instance.title:
            existing = (
                self.get_model()
                .objects.filter(directory=directory, title=new_title)
                .exclude(pk=instance.pk)
                .first()
            )
            if existing:
                raise ValidationError({"title": f"目录下已存在「{new_title}」"})

        data["updated_by"] = user
        extra = self._prepare_extra_fields(data, instance)
        for k, v in extra.items():
            setattr(instance, k, v)
        serializer.save(**{k: v for k, v in data.items() if k not in extra})

    def perform_destroy(self, instance):
        if instance.locked:
            raise PermissionDenied("该用例已被创建者锁定，禁止删除")
        user = _user_id(self.request)
        if instance.visibility == "hidden" and instance.created_by != user:
            raise PermissionDenied("没有删除权限")
        delete_case(instance.id)

    def _prepare_extra_fields(self, data, instance=None):
        extra = {}
        for field_name in ["permitted_users", "permitted_editors"]:
            if field_name in data:
                val = data.pop(field_name)
                extra[field_name] = (
                    json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else val
                )
        return extra

    @action(detail=False, methods=["post"], url_path="batch")
    def batch_import(self, request):
        """POST /{type}/definitions/batch/ — batch import cases."""
        model = self.get_model()
        user = _user_id(request)
        items = request.data if isinstance(request.data, list) else request.data.get("items", [])
        if not items:
            return Response({"message": "items is required"}, status=400)

        created = 0
        updated = 0
        errors = []
        for item in items:
            item_id = item.get("id")
            title = item.get("title", "").strip()
            if not title:
                errors.append({"item": item, "error": "标题不能为空"})
                continue
            fields = {
                "title": title,
                "category": item.get("category", ""),
                "priority": item.get("priority", "P1"),
                "enabled": item.get("enabled", True),
                "created_by": user,
                "updated_by": user,
                "directory_id": item.get("directory_id"),
            }
            if "steps_data" in item:
                fields["steps_data"] = item["steps_data"]
            if "config_json" in item:
                fields["config_json"] = item["config_json"]
            if "url" in item:
                fields["url"] = item.get("url", "")

            is_new = not model.objects.filter(id=item_id).exists()
            try:
                _SAVE_FN[model](item_id, **fields)
                if is_new:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({"item": item, "error": str(e)})

        return Response({"created": created, "updated": updated, "errors": errors})


# ═══════════════════════════════════════════════════════
# CaseDirectoryViewSet
# ═══════════════════════════════════════════════════════


class CaseDirectoryViewSet(viewsets.ModelViewSet):
    """Two-level directory CRUD + batch-move + permission."""

    serializer_class = CaseDirectorySerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        qs = CaseDirectory.objects.prefetch_related("children").order_by("sort_order", "id")
        case_type = self.request.query_params.get("case_type")
        if case_type:
            qs = qs.filter(case_type=case_type)
        return qs

    def list(self, request, *args, **kwargs):
        case_type = request.query_params.get("case_type")
        qs = self.get_queryset().filter(parent__isnull=True)
        if case_type:
            qs = qs.filter(case_type=case_type)
        tree = CaseDirectorySerializer(qs, many=True).data
        return Response({"directories": tree})

    def perform_create(self, serializer):
        data = serializer.validated_data
        parent = data.get("parent")
        if parent and parent.parent_id is not None:
            raise ValidationError({"parent": "只支持两级目录"})
        user = _user_id(self.request)
        serializer.save(created_by=user)

    def perform_destroy(self, instance):
        user = _user_id(self.request)
        ok, result = api_directories.delete_directory(instance.id, deleted_by=user)
        if not ok:
            raise PermissionDenied(
                result if isinstance(result, str) else result.get("message", "删除失败")
            )

    @action(detail=False, methods=["post"], url_path="batch-move")
    def batch_move(self, request):
        case_ids = request.data.get("case_ids", [])
        dir_ids = request.data.get("dir_ids", [])
        target_dir_id = request.data.get("target_directory_id")

        items = [{"type": "case", "id": cid} for cid in case_ids] + [
            {"type": "directory", "id": did} for did in dir_ids
        ]
        result = api_directories.batch_move_items(items, target_dir_id)
        return Response(result)

    @action(detail=True, methods=["post"], url_path="permission")
    def set_permission(self, request, pk=None):
        directory = self.get_object()
        user = _user_id(request)
        if directory.created_by and directory.created_by != user:
            raise PermissionDenied("只有创建者可以修改权限")

        ok, result = api_directories.update_directory_permission(
            directory.id,
            allow_create=request.data.get("allow_create"),
            allow_delete=request.data.get("allow_delete"),
        )
        if not ok:
            raise ValidationError({"detail": result})
        directory.refresh_from_db()
        return Response(CaseDirectorySerializer(directory).data)


# ═══════════════════════════════════════════════════════
# Concrete Case ViewSets
# ═══════════════════════════════════════════════════════


class UiCaseViewSet(BaseCaseViewSet):
    model = TestDefinition
    id_prefix = "TC"
    serializer_class = TestDefinitionSerializer


class ApiCaseViewSet(BaseCaseViewSet):
    model = ApiTestCase
    id_prefix = "API"
    serializer_class = ApiTestCaseSerializer


class StorageCaseViewSet(BaseCaseViewSet):
    model = StorageTestCase
    id_prefix = "ST"
    serializer_class = StorageTestCaseSerializer


class WebCaseViewSet(BaseCaseViewSet):
    model = WebTestCase
    id_prefix = "WEB"
    serializer_class = WebTestCaseSerializer


# ═══════════════════════════════════════════════════════
# CaseActionsViewSet (shared lock / unlock / visibility)
# ═══════════════════════════════════════════════════════


class CaseActionsViewSet(viewsets.GenericViewSet):
    """Shared lock/unlock/visibility — works across all 4 case types."""

    lookup_field = "case_id"
    lookup_value_regex = r"[-\w]+"

    @action(detail=True, methods=["post"], url_path="lock")
    def acquire_lock(self, request, case_id=None):
        user = _user_id(request)
        force = request.data.get("force") in (True, "true", "True")
        ok, result = acquire_edit_lock(case_id, user, force=force)
        if not ok:
            _raise_lock_error(result)
        return Response({"locked": True, "editing_by": result["editing_by"]})

    @action(detail=True, methods=["post"], url_path="unlock")
    def release_lock(self, request, case_id=None):
        user = _user_id(request)
        force = request.data.get("force") in (True, "true", "True")
        ok, result = release_edit_lock(case_id, user, force=force)
        if not ok:
            _raise_lock_error(result)
        return Response({"unlocked": True})

    @action(detail=True, methods=["post"], url_path="case-lock")
    def case_lock(self, request, case_id=None):
        user = _user_id(request)
        ok, result = set_case_lock(case_id, user, locked=True)
        if not ok:
            _raise_lock_error(result)
        return Response({"locked": True})

    @action(detail=True, methods=["post"], url_path="case-unlock")
    def case_unlock(self, request, case_id=None):
        user = _user_id(request)
        ok, result = set_case_lock(case_id, user, locked=False)
        if not ok:
            _raise_lock_error(result)
        return Response({"unlocked": True})

    @action(detail=True, methods=["post"], url_path="visibility")
    def set_visibility(self, request, case_id=None):
        user = _user_id(request)
        ok, result = set_case_visibility(
            case_id,
            user,
            visibility=request.data.get("visibility", "public"),
            permitted_users=request.data.get("permitted_users"),
            permitted_editors=request.data.get("permitted_editors"),
            permission=request.data.get("permission"),
        )
        if not ok:
            _raise_lock_error(result)
        return Response({"visibility": result["visibility"]})
