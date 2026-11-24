from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from . import api as case_api
from .api_projects import ConflictError
from .models import CaseProject


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


@extend_schema_view(
    list=extend_schema(responses=OpenApiTypes.ANY, operation_id="cases_projects_list"),
    create=extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT),
    retrieve=extend_schema(responses=OpenApiTypes.OBJECT),
    partial_update=extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT),
    destroy=extend_schema(responses=OpenApiTypes.OBJECT),
)
class CaseProjectViewSet(viewsets.ViewSet):
    queryset = CaseProject.objects.none()

    def list(self, request):
        return Response(case_api.list_projects(user_id=_user_id(request)))

    def create(self, request):
        body = request.data or {}
        try:
            data = case_api.create_project(
                name=body.get("name", ""),
                description=body.get("description", ""),
                library_kind=body.get("library_kind", ""),
                user_id=_user_id(request),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            data = case_api.get_sheet(project_id=int(pk), user_id=_user_id(request))
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
                library_kind=body.get("library_kind"),
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

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["post"], url_path="rows")
    def add_row(self, request, pk=None):
        body = request.data or {}
        try:
            data = case_api.create_row(
                project_id=int(pk),
                user_id=_user_id(request),
                title=body.get("title", ""),
                priority=body.get("priority", "P1"),
                system=body.get("system", "ANDROID"),
                business_type=body.get("business_type", "appliance"),
                module=body.get("module", ""),
                precondition=body.get("precondition", ""),
                steps=body.get("steps"),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[OpenApiParameter("case_id", OpenApiTypes.STR, OpenApiParameter.PATH)],
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    @action(detail=True, methods=["patch"], url_path=r"rows/(?P<case_id>[^/.]+)")
    def edit_row(self, request, pk=None, case_id=None):
        try:
            data = case_api.update_row(
                project_id=int(pk),
                case_id=case_id,
                user_id=_user_id(request),
                **(request.data or {}),
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    @extend_schema(
        parameters=[OpenApiParameter("case_id", OpenApiTypes.STR, OpenApiParameter.PATH)],
        responses=OpenApiTypes.OBJECT,
    )
    @action(detail=True, methods=["delete"], url_path=r"rows/(?P<case_id>[^/.]+)")
    def remove_row(self, request, pk=None, case_id=None):
        try:
            case_api.delete_row(project_id=int(pk), case_id=case_id, user_id=_user_id(request))
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response({"id": case_id})

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["post"], url_path="import-yaml")
    def import_yaml(self, request, pk=None):
        uploaded = request.FILES.get("file")
        text = (
            uploaded.read().decode("utf-8")
            if uploaded
            else str((request.data or {}).get("text") or "")
        )
        try:
            data = case_api.import_yaml_text(
                project_id=int(pk),
                user_id=_user_id(request),
                text=text,
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["put"], url_path="view")
    def save_view(self, request, pk=None):
        try:
            data = case_api.save_sheet_view(
                project_id=int(pk),
                user_id=_user_id(request),
                payload=request.data or {},
            )
        except Exception as exc:
            return _raise_or_conflict(exc)
        return Response(data)

    @extend_schema(responses=OpenApiTypes.ANY)
    @action(detail=False, methods=["get"], url_path="automation")
    def automation(self, request):
        return Response(case_api.list_automation_projects(user_id=_user_id(request)))
