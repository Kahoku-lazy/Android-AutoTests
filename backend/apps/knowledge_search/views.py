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

import random

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_superuser

from . import api, eval_runner, retrieval
from .serializers import (
    EvalQuerySerializer,
    EvalRunSerializer,
    EvalTriggerSerializer,
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


class EvalRunningConflict(APIException):
    """同模块已有进行中的评测：409。"""

    status_code = 409
    default_detail = "该模块已有进行中的评测"
    default_code = "eval_running"


class EvalRunListAPIView(APIView):
    """GET 评测运行列表（登录可读）；POST 触发自动评测（仅超管）。"""

    @extend_schema(operation_id="knowledge_search_evaluations_list", responses=OpenApiTypes.OBJECT)
    def get(self, request):
        runs = api.list_eval_runs(request.query_params.get("module", ""))
        return Response({"runs": EvalRunSerializer(runs, many=True).data})

    @extend_schema(
        operation_id="knowledge_search_evaluations_create",
        request=EvalTriggerSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        _require_superuser(request)
        serializer = EvalTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        module = api.get_module(data["module_id"])
        if module is None:
            raise NotFound("模块不存在")
        if not module.enabled:
            raise ValidationError("模块已禁用，不能评测")
        if data["pos_count"] + data["neg_count"] > 100:
            raise ValidationError("题量超过上限 100")
        if api.running_eval_run(module.name) is not None:
            raise EvalRunningConflict()
        # 跨 App 只读 Model：运营模型配置（规则允许的读路径）。
        from backend.apps.ai_assistant.models import AIModelConfig

        model_config = AIModelConfig.objects.filter(
            pk=data["model_config_id"], model_kind="chat"
        ).first()
        if model_config is None:
            raise ValidationError("模型配置不存在或不是 chat 类")
        run = api.create_eval_run(
            module_name=module.name,
            module_snapshot={
                "name": module.name,
                "description": module.description,
                "data_dir": module.data_dir,
                "enabled": module.enabled,
            },
            model_config_id=model_config.pk,
            model_snapshot={
                "provider": model_config.provider,
                "api_key_env": model_config.api_key_env,
                "model_name": model_config.model_name,
                "base_url": model_config.base_url,
            },
            pos_count=data["pos_count"],
            neg_count=data["neg_count"],
            seed=random.randrange(1, 2**31),
            cost_estimate=eval_runner.estimate_cost(data["pos_count"], data["neg_count"]),
        )
        eval_runner.start_eval_run(run.pk)
        return Response(EvalRunSerializer(run).data, status=201)


class EvalRunDetailAPIView(APIView):
    """GET 评测运行详情（登录可读）：进度 / 指标 / 逐题明细。"""

    @extend_schema(
        operation_id="knowledge_search_evaluations_detail", responses=OpenApiTypes.OBJECT
    )
    def get(self, request, pk: int):
        run = api.get_eval_run(int(pk))
        if run is None:
            raise NotFound("评测运行不存在")
        payload = EvalRunSerializer(run).data
        payload["queries"] = EvalQuerySerializer(run.queries.all(), many=True).data
        return Response(payload)
