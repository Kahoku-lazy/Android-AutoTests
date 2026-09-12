"""element_locator DRF views — locator projects / directories / move / batch-delete."""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.response import Response

from . import api as el_api
from .api_projects import ConflictError

_GONE_MSG = "分组树写接口已停用，请改用项目目录 API"


def _raise_or_conflict(exc: Exception) -> Response:
    if isinstance(exc, LookupError):
        raise NotFound(str(exc)) from exc
    if isinstance(exc, ConflictError):
        return Response({"message": exc.message}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, ValueError):
        raise ValidationError({"detail": str(exc)}) from exc
    raise exc


class LocatorProjectViewSet(viewsets.ViewSet):
    """System-locked projects: list / retrieve / tree. Mutations → 405."""

    lookup_field = "code"
    lookup_value_regex = "android|web|api"

    def list(self, request):
        return Response(el_api.list_projects())

    def retrieve(self, request, code=None):
        obj = el_api.get_project_by_code(code=code or "")
        if obj is None:
            raise NotFound("项目不存在")
        return Response(el_api.serialize_project(obj))

    def create(self, request):
        raise MethodNotAllowed("POST", detail="系统项目不可新建")

    def partial_update(self, request, code=None):
        raise MethodNotAllowed("PATCH", detail="系统项目不可改名")

    def destroy(self, request, code=None):
        raise MethodNotAllowed("DELETE", detail="系统项目不可删除")

    @action(detail=True, methods=["get"], url_path="tree")
    def tree(self, request, code=None):
        try:
            data = el_api.get_project_tree(code=code or "")
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)


class LocatorDirectoryViewSet(viewsets.ViewSet):
    """Directory create / update / delete."""

    def create(self, request):
        body = request.data or {}
        parent_id = body.get("parent_id")
        try:
            data = el_api.create_directory(
                project_code=str(body.get("project_code") or ""),
                name=body.get("name", ""),
                parent_id=int(parent_id) if parent_id is not None else None,
                sort_order=int(body.get("sort_order") or 0),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        body = request.data or {}
        try:
            data = el_api.update_directory(
                directory_id=int(pk),
                name=body.get("name"),
                sort_order=body.get("sort_order"),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    def destroy(self, request, pk=None):
        try:
            el_api.delete_directory(directory_id=int(pk))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": int(pk)})


@api_view(["POST"])
def move_items(request):
    body = request.data or {}
    parent_id = body.get("parent_directory_id", body.get("parent_id"))
    try:
        data = el_api.move_item(
            kind=str(body.get("kind") or ""),
            item_id=int(body.get("id")),
            parent_directory_id=int(parent_id) if parent_id is not None else None,
            sort_order=int(body.get("sort_order") or 0),
        )
    except Exception as exc:
        return _raise_or_conflict(exc)
    return Response(data)


@api_view(["POST"])
def batch_delete_files(request):
    body = request.data or {}
    ids = body.get("ids") or []
    try:
        data = el_api.batch_delete_files(kind=str(body.get("kind") or ""), ids=[int(i) for i in ids])
    except Exception as exc:
        return _raise_or_conflict(exc)
    return Response(data)


def group_write_gone(_request, *args, **kwargs):
    """410 Gone for legacy group write endpoints."""
    return Response({"status": False, "message": _GONE_MSG}, status=status.HTTP_410_GONE)
