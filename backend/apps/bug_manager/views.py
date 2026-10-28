"""bug-manager DRF views — list, detail, status update and historical sync."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.bug_manager import api
from backend.apps.bug_manager.serializers import BugListQuerySerializer, BugStatusInputSerializer


def _user_id(request) -> str:
    """Current request user id as a string."""
    return str(getattr(request, "user_id", "") or "")


class BugListAPIView(APIView):
    """GET /api/bugs/ — visible BUG tickets with summary counters."""

    @extend_schema(
        tags=["bugs"],
        operation_id="bug_ticket_list",
        parameters=[
            OpenApiParameter("category", OpenApiTypes.STR, required=False),
            OpenApiParameter("status", OpenApiTypes.STR, required=False),
            OpenApiParameter("keyword", OpenApiTypes.STR, required=False),
        ],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        serializer = BugListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            payload = api.list_bugs(
                _user_id(request),
                category=data.get("category") or "",
                status=data.get("status") or "",
                keyword=data.get("keyword") or "",
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload)


class BugDetailAPIView(APIView):
    """GET / PATCH /api/bugs/{id}/ — full detail or processing status."""

    @extend_schema(tags=["bugs"], operation_id="bug_ticket_detail", responses=OpenApiTypes.OBJECT)
    def get(self, request, bug_id: int):
        row = api.get_bug(_user_id(request), bug_id)
        if row is None:
            raise NotFound("BUG 单不存在")
        return Response(row)

    @extend_schema(
        tags=["bugs"],
        operation_id="bug_ticket_update_status",
        request=BugStatusInputSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def patch(self, request, bug_id: int):
        serializer = BugStatusInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = api.update_bug_status(
            _user_id(request),
            bug_id,
            serializer.validated_data["status"],
        )
        if row is None:
            raise NotFound("BUG 单不存在")
        return Response(row)


class BugSyncAPIView(APIView):
    """POST /api/bugs/sync/ — backfill BUG tickets from visible task errors."""

    @extend_schema(
        tags=["bugs"],
        operation_id="bug_ticket_sync",
        request=None,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        return Response(api.sync_visible_tasks(_user_id(request)))
