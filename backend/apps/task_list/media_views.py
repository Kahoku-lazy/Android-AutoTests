from __future__ import annotations

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.task_list import api, media_links


def media_response(request, media: dict) -> HttpResponse:
    etag = f'"{media["sha256"]}"'
    if request.headers.get("If-None-Match") == etag:
        response = HttpResponse(status=304)
    else:
        response = HttpResponse(media["data"], content_type=media["media_type"])
        response["ETag"] = etag
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


class TaskMediaLinkAPIView(APIView):
    @extend_schema(
        tags=["tasks"],
        request=None,
        responses=OpenApiTypes.OBJECT,
        operation_id="task_media_link",
    )
    def post(self, request, task_id: int, media_id: int):
        user_id = getattr(request, "user_id", None)
        link = api.create_task_media_link(user_id, task_id, media_id)
        if link is None:
            raise NotFound("图片不存在")
        return Response(link)


class SignedTaskMediaAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["tasks"],
        operation_id="task_media_signed",
        responses={(200, "image/webp"): OpenApiTypes.BINARY},
    )
    def get(self, request, task_id: int, media_id: int, expires: int, signature: str):
        if not media_links.verify(task_id, media_id, expires, signature):
            raise PermissionDenied("链接无效或已过期")
        media = api.get_media_by_id(task_id, media_id)
        if media is None:
            raise NotFound("图片不存在")
        payload = api.media_payload(media)
        if payload is None:
            raise NotFound("图片不存在")
        return media_response(request, payload)
