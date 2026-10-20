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

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api, engine_adapter
from .models import AIAgent, AITask
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
    TaskSubmitInputSerializer,
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


# ═══════════════════════════════════════════════════════════════════
# 任务发布（POST /api/ai/tasks/submit · GET /api/ai/agent-tasks · POST /api/ai/agent-tasks/{id}/delete）
# ═══════════════════════════════════════════════════════════════════


class TaskSubmitAPIView(APIView):
    """POST /api/ai/tasks/submit — 提交任务；按设备调度（同设备排队 / 异设备并行）。"""

    @extend_schema(request=TaskSubmitInputSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TaskSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agent = api.get_agent(data["agent_id"])
        if agent is None:
            raise ValidationError("智能体不存在或不可用")
        try:
            engine_adapter.sop_role_models(agent)
        except ValueError as exc:
            raise ValidationError(f"智能体不可用于 SOP：{exc}") from exc

        title = data["title"]
        goal = (data.get("goal") or "").strip()
        device_serial = (data.get("device_serial") or "").strip()
        device_label = (data.get("device_label") or "").strip()
        case_title = (data.get("case_title") or "").strip()

        from .attachments import AttachmentError, collect_task_files, store_flat_upload

        try:
            prepared = collect_task_files(
                request.FILES.getlist("config"),
                request.FILES.getlist("documents"),
            )
        except AttachmentError as exc:
            raise ValidationError(str(exc)) from exc

        task = api.create_task(
            agent,
            title=title,
            goal=goal,
            device_serial=device_serial,
            device_label=device_label,
            case_title=case_title,
        )
        for index, item in enumerate(prepared):
            api.add_task_attachment(
                task,
                kind=item.kind,
                filename=item.filename,
                body=item.body,
                sort_order=index,
                stored_path=store_flat_upload(item.filename, item.content),
            )
        api.dispatch_device(device_serial)
        task.refresh_from_db()
        return Response({"id": task.id, "status": task.status, "result": ""})


class AgentTaskListAPIView(APIView):
    """GET /api/ai/agent-tasks — 任务发布列表（AITask）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        agent = api.get_platform_agent()
        if agent is None:
            return Response({"tasks": []})
        tasks = AITask.objects.filter(agent=agent).select_related("agent").order_by("-id")[:100]
        return Response({"tasks": [api.serialize_agent_task_row(t) for t in tasks]})


class AgentTaskDeleteAPIView(APIView):
    """POST /api/ai/agent-tasks/{task_id}/delete — 删除任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        agent = api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = AITask.objects.get(id=task_id, agent=agent)
        except AITask.DoesNotExist:
            raise NotFound("任务不存在")
        api.delete_task(task)
        return Response({})


class AgentTaskCancelAPIView(APIView):
    """POST /api/ai/agent-tasks/{task_id}/cancel — 关闭运行中的 SOP。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        agent = api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = AITask.objects.get(id=task_id, agent=agent)
        except AITask.DoesNotExist:
            raise NotFound("任务不存在")
        try:
            task = api.cancel_running_task(task)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"id": task.id, "status": task.status})


class AgentTaskRerunAPIView(APIView):
    """POST /api/ai/agent-tasks/{task_id}/rerun — 失败任务克隆新建并调度。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        from models.constants import TaskStatus

        agent = api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = AITask.objects.select_related("agent").get(id=task_id, agent=agent)
        except AITask.DoesNotExist:
            raise NotFound("任务不存在")
        if task.status != TaskStatus.FAILED:
            raise ValidationError("仅失败任务可重新执行")
        new_task = api.rerun_task(task)
        api.dispatch_device(new_task.device_serial or "")
        new_task.refresh_from_db()
        return Response({"id": new_task.id, "status": new_task.status})


class AgentTaskClearAPIView(APIView):
    """POST /api/ai/agent-tasks/clear — 调试：清空全部任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        agent = api.get_platform_agent()
        if agent is None:
            return Response({"deleted": 0})
        deleted = api.clear_agent_tasks(agent)
        return Response({"deleted": deleted})


class AgentTaskDetailAPIView(APIView):
    """GET /api/ai/agent-tasks/{task_id} — 任务发布详情（过程日志）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT, operation_id="ai_agent_task_detail")
    def get(self, request, task_id: int):
        agent = api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = AITask.objects.select_related("agent").get(id=task_id, agent=agent)
        except AITask.DoesNotExist:
            raise NotFound("任务不存在")
        return Response(api.serialize_agent_task_detail(task))
