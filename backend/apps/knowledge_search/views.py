"""知识库检索 HTTP 面（JWT）：模块登记 / 多选提问 / 预建索引。

GET    /api/knowledge-search/modules/              登录可读：模块列表
POST   /api/knowledge-search/modules/              仅超管：新增模块（=新增资料路径）
PATCH  /api/knowledge-search/modules/<int:pk>/     仅超管：编辑模块（含改路径与启停）
DELETE /api/knowledge-search/modules/<int:pk>/     仅超管：删除模块登记
POST   /api/knowledge-search/modules/<int:pk>/index/  仅超管：预建增量索引
POST   /api/knowledge-search/query/                登录可用：勾选模块提问，返回检索原文

响应信封由全局 EnvelopeJSONRenderer 统一包 {status, data}；
检索三态（ok/no_hit/unavailable）是业务结果，HTTP 仍 200。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_superuser

from . import api, retrieval
from .serializers import (
    KnowledgeModuleSerializer,
    ModulePatchSerializer,
    ModuleWriteSerializer,
    QuerySerializer,
)


def _user_id(request) -> str:
    """取网关注入的用户 ID。"""
    return str(getattr(request, "user_id", "") or "")


def _require_superuser(request) -> None:
    """非超管一律 403。"""
    if not is_superuser(_user_id(request)):
        raise PermissionDenied("Forbidden")


def _module_or_404(pk: int):
    """按主键取模块；不存在给 404。"""
    module = api.get_module(int(pk))
    if module is None:
        raise NotFound("模块不存在")
    return module


class KnowledgeModuleListAPIView(APIView):
    """GET 模块列表（登录可读）；POST 新增模块（仅超管）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        modules = KnowledgeModuleSerializer(api.list_modules(), many=True).data
        return Response({"modules": modules})

    @extend_schema(request=ModuleWriteSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        _require_superuser(request)
        serializer = ModuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            module = api.create_module(**serializer.validated_data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(KnowledgeModuleSerializer(module).data, status=201)


class KnowledgeModuleDetailAPIView(APIView):
    """PATCH 编辑 / DELETE 删除模块登记（仅超管）。"""

    @extend_schema(request=ModulePatchSerializer, responses=OpenApiTypes.OBJECT)
    def patch(self, request, pk: int):
        _require_superuser(request)
        _module_or_404(pk)
        serializer = ModulePatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data:
            raise ValidationError("至少提供一个要修改的字段")
        try:
            module = api.update_module(int(pk), **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(KnowledgeModuleSerializer(module).data)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, pk: int):
        _require_superuser(request)
        _module_or_404(pk)
        api.delete_module(int(pk))
        return Response({"deleted": True})


class KnowledgeModuleIndexAPIView(APIView):
    """POST 预建索引（仅超管）：同步增量重建，返回重建文件数。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk: int):
        _require_superuser(request)
        module = _module_or_404(pk)
        outcome = retrieval.index_module(name=module.name)
        return Response(
            {
                "ok": outcome["status"],
                "error": outcome["error"],
                "reindexed": outcome["reindexed"],
            }
        )


class KnowledgeQueryAPIView(APIView):
    """POST 多选提问（登录可用）：返回检索原文与三态结果。"""

    @extend_schema(request=QuerySerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = retrieval.search(
            question=data["question"],
            bases=data["bases"],
            top_k=data.get("top_k"),
        )
        return Response(result)
