"""case_manager DRF ViewSets — projects, directories, document definitions."""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from . import api as case_api
from .api_projects import ConflictError


def _user_id(request) -> str:
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return str(uid)
    user = getattr(request, "user", None)
    if user and getattr(user, "id", None) is not None:
        return str(user.id)
    return ""


def _raise_or_conflict(exc: Exception) -> Response:
    if isinstance(exc, LookupError):
        raise NotFound(str(exc)) from exc
    if isinstance(exc, ConflictError):
        return Response({"message": exc.message}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, ValueError):
        raise ValidationError({"detail": str(exc)}) from exc
    raise exc


class CaseProjectViewSet(viewsets.ViewSet):
    """Project list / create / detail / update / delete / tree."""

    def list(self, request):
        return Response(case_api.list_projects(user_id=_user_id(request)))

    def create(self, request):
        body = request.data or {}
        try:
            data = case_api.create_project(
                name=body.get("name", ""),
                description=body.get("description", ""),
                user_id=_user_id(request),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            obj = case_api.get_project(project_id=int(pk), user_id=_user_id(request))
            if obj is None:
                raise LookupError("项目不存在")
            data = case_api.serialize_project(obj)
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def partial_update(self, request, pk=None):
        body = request.data or {}
        try:
            data = case_api.update_project(
                project_id=int(pk),
                user_id=_user_id(request),
                name=body.get("name"),
                description=body.get("description"),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def destroy(self, request, pk=None):
        try:
            case_api.delete_project(project_id=int(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": int(pk)})

    @action(detail=True, methods=["get"], url_path="tree")
    def tree(self, request, pk=None):
        try:
            data = case_api.get_project_tree(project_id=int(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)


class CaseDirectoryViewSet(viewsets.ViewSet):
    """Directory create / update / delete."""

    def create(self, request):
        body = request.data or {}
        parent_id = body.get("parent_id")
        try:
            data = case_api.create_directory(
                project_id=int(body.get("project_id")),
                name=body.get("name", ""),
                user_id=_user_id(request),
                parent_id=int(parent_id) if parent_id is not None else None,
                sort_order=int(body.get("sort_order") or 0),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        body = request.data or {}
        try:
            data = case_api.update_directory(
                directory_id=int(pk),
                user_id=_user_id(request),
                name=body.get("name"),
                sort_order=body.get("sort_order"),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def destroy(self, request, pk=None):
        try:
            case_api.delete_directory(directory_id=int(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": int(pk)})


class CaseFileViewSet(viewsets.ViewSet):
    """Case sheet (tree file) CRUD + Excel rows payload."""

    def create(self, request):
        body = request.data or {}
        directory_id = body.get("directory_id")
        try:
            data = case_api.create_file(
                project_id=int(body.get("project_id")),
                name=body.get("name", ""),
                user_id=_user_id(request),
                directory_id=int(directory_id) if directory_id is not None else None,
                sort_order=int(body.get("sort_order") or 0),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            data = case_api.get_file_sheet(file_id=int(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def partial_update(self, request, pk=None):
        body = request.data or {}
        try:
            data = case_api.update_file(
                file_id=int(pk),
                user_id=_user_id(request),
                name=body.get("name"),
                sort_order=body.get("sort_order"),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def destroy(self, request, pk=None):
        try:
            case_api.delete_file(file_id=int(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": int(pk)})


class TestDefinitionViewSet(viewsets.ViewSet):
    """Document case CRUD + batch-delete."""

    def create(self, request):
        body = request.data or {}
        if body.get("file_id") is None:
            raise ValidationError({"file_id": "必须指定所属文件"})
        if body.get("project_id") is None:
            raise ValidationError({"project_id": "必须指定所属项目"})
        try:
            data = case_api.create_definition(
                project_id=int(body.get("project_id")),
                file_id=int(body.get("file_id")),
                user_id=_user_id(request),
                title=body.get("title", ""),
                test_type=body.get("test_type", "app"),
                business_type=body.get("business_type", "appliance"),
                module=body.get("module", ""),
                precondition=body.get("precondition", ""),
                steps=body.get("steps", ""),
                expected_result=body.get("expected_result", ""),
                sort_order=int(body.get("sort_order") or 0),
                require_fields=bool(body.get("require_fields")),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            data = case_api.get_definition(case_id=str(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def partial_update(self, request, pk=None):
        body = request.data or {}
        kwargs = {
            "case_id": str(pk),
            "user_id": _user_id(request),
            "require_fields": body.get("require_fields", True),
        }
        for key in (
            "title",
            "test_type",
            "business_type",
            "module",
            "precondition",
            "steps",
            "expected_result",
            "sort_order",
        ):
            if key in body:
                kwargs[key] = body.get(key)
        try:
            data = case_api.update_definition(**kwargs)
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def destroy(self, request, pk=None):
        try:
            case_api.delete_definition(case_id=str(pk), user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": str(pk)})

    @action(detail=False, methods=["post"], url_path="batch-delete")
    def batch_delete(self, request):
        body = request.data or {}
        try:
            data = case_api.batch_delete_definitions(
                case_ids=body.get("ids") or body.get("case_ids") or [],
                user_id=_user_id(request),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)


@api_view(["POST"])
def move_items(request):
    """Move directory or file within a project tree."""
    body = request.data or {}
    target = body.get("target_directory_id", body.get("parent_id"))
    try:
        data = case_api.move_item(
            user_id=_user_id(request),
            item_type=body.get("item_type") or body.get("type") or "",
            item_id=body.get("item_id") or body.get("id"),
            target_directory_id=int(target) if target is not None else None,
            sort_order=int(body.get("sort_order") or 0),
            project_id=int(body["project_id"]) if body.get("project_id") is not None else None,
        )
    except Exception as exc:
        return _raise_or_conflict(exc)
    return Response(data)
