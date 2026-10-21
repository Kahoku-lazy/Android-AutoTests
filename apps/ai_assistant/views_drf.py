"""ai-assistant DRF views — Agent 组（Batch 1 迁移）。

路径与方法保持旧契约不变（等行为迁移）：
  GET  /api/ai/agents                    列表（按 owner 过滤）
  POST /api/ai/agents/create             创建
  GET  /api/ai/agents/{id}               详情（api_key 脱敏）
  POST /api/ai/agents/{id}/update        更新
  POST /api/ai/agents/{id}/delete        删除
  POST /api/ai/agents/{id}/reveal-key    一次性查看 Key

鉴权：JWT 中间件已先校验并注入 request.user_id；DRF 全局 IsAuthenticated 兜底。
对象级权限：复用 permissions.py 函数（行为与旧视图完全一致，
包括「权限检查先于存在性检查 → 不存在资源返回 403」）。
写库：全部经 api.py。
"""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from . import api
from .models import AIAgent
from .permissions import (
    check_agent_owner,
    check_agent_visible,
    check_can_create_agent,
    check_can_update_agent,
    filter_agents_for_user,
)
from .serializers import (
    AgentDetailSerializer,
    AgentInputSerializer,
    AgentListSerializer,
)

_MODEL_LIST_PATHS = ["/models", "/v1/models"]


def _user_id(request) -> str:
    """用户 id：优先中间件注入的 request.user_id，回退 DRF request.user.id。"""
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return str(uid)
    user = getattr(request, "user", None)
    if user is not None and hasattr(user, "id"):
        return str(user.id)
    return ""


def _agent_pk(request) -> int | None:
    """解析路由 pk 为 int；非数字返回 None（旧路由 int 转换器下即 404）。"""
    raw = str(request.parser_context["kwargs"]["pk"])
    return int(raw) if raw.isdigit() else None


# ═══════════════════════════════════════════════════════════════════
# Agent ViewSet
# ═══════════════════════════════════════════════════════════════════


class AgentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Agent 资源 — 路径与旧函数视图一一对应（见模块 docstring）。"""

    queryset = AIAgent.objects.all()
    serializer_class = AgentDetailSerializer

    def _require_owner(self, request) -> int:
        """返回当前用户拥有的 agent_id；权限检查失败 → 403（含资源不存在）。"""
        agent_id = _agent_pk(request)
        if agent_id is None:
            raise NotFound("not found")
        if not check_agent_owner(_user_id(request), agent_id):
            raise PermissionDenied("Forbidden")
        return agent_id

    def _require_visible(self, request) -> int:
        """返回当前用户可见的 agent_id（owner 或共享智能体）；否则 403。"""
        agent_id = _agent_pk(request)
        if agent_id is None:
            raise NotFound("not found")
        if not check_agent_visible(_user_id(request), agent_id):
            raise PermissionDenied("Forbidden")
        return agent_id

    def _require_admin(self, request) -> int:
        """仅超级管理员可写：非超管 403；超管但资源不存在 404。"""
        agent_id = _agent_pk(request)
        if agent_id is None:
            raise NotFound("not found")
        if not check_can_update_agent(_user_id(request), agent_id):
            raise PermissionDenied("Forbidden")
        if not AIAgent.objects.filter(id=agent_id).exists():
            raise NotFound("not found")
        return agent_id

    # ── 列表 ──

    def list(self, request, *args, **kwargs):
        qs = filter_agents_for_user(AIAgent.objects.all(), _user_id(request))
        return Response({"agents": AgentListSerializer(qs, many=True).data})

    # ── 详情 ──

    def retrieve(self, request, *args, **kwargs):
        agent_id = self._require_visible(request)
        a = AIAgent.objects.get(id=agent_id)
        return Response({"agent": AgentDetailSerializer(a, context={"request": request}).data})

    # ── 创建 ──

    @action(detail=False, methods=["post"], url_path="create")
    def create_agent(self, request, *args, **kwargs):
        if not check_can_create_agent(_user_id(request)):
            raise PermissionDenied("Forbidden")
        serializer = AgentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = api.create_agent(_user_id(request), serializer.validated_data)
        return Response({"id": agent.id})

    # ── 更新 ──

    @action(detail=True, methods=["post"], url_path="update")
    def update_agent(self, request, *args, **kwargs):
        agent_id = self._require_admin(request)
        serializer = AgentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = api.update_agent(AIAgent.objects.get(id=agent_id), serializer.validated_data)
        return Response({"id": agent.id})

    # ── 删除 ──

    @action(detail=True, methods=["post"], url_path="delete")
    def delete_agent(self, request, *args, **kwargs):
        agent_id = self._require_admin(request)
        api.delete_agent(AIAgent.objects.get(id=agent_id))
        return Response({})

    # ── 一次性查看 Key ──

    @action(detail=True, methods=["post"], url_path="reveal-key")
    def reveal_key(self, request, *args, **kwargs):
        agent_id = self._require_admin(request)
        a = AIAgent.objects.get(id=agent_id)
        try:
            payload = api.reveal_agent_key(a)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(payload)
