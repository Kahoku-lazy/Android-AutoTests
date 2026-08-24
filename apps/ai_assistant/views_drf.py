"""ai-assistant DRF views — Agent 组（Batch 1 迁移）。

路径与方法保持旧契约不变（等行为迁移）：
  GET  /api/ai/agents                    列表（按 owner 过滤）
  POST /api/ai/agents/create             创建
  GET  /api/ai/agents/{id}               详情（api_key 脱敏）
  POST /api/ai/agents/{id}/update        更新
  POST /api/ai/agents/{id}/delete        删除
  POST /api/ai/agents/{id}/reveal-key    一次性查看 Key
  GET  /api/ai/agents/health             全部 Agent 健康检查
  POST /api/ai/agents/{id}/test          连接测试
  GET  /api/ai/agents/{id}/models        缓存模型列表
  POST /api/ai/models/detect             模型探测（GET 分支保持 400 语义）
  GET  /api/ai/available-tools           平台工具
  GET  /api/ai/available-skills          workspace 技能

鉴权：JWT 中间件已先校验并注入 request.user_id；DRF 全局 IsAuthenticated 兜底。
对象级权限：复用 permissions.py 函数（行为与旧视图完全一致，
包括「权限检查先于存在性检查 → 不存在资源返回 403」）。
写库：全部经 api.py。
"""

import json
import logging

from datetime import datetime

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api
from .agent_scope.provider_registry import get_provider_config
from .models import AIAgent, AIConversation, AIMessage
from .permissions import (
    check_agent_owner,
    check_can_create_agent,
    check_conversation_access,
    filter_agents_for_user,
    filter_conversations_for_user,
)
from .serializers import (
    AgentDetailSerializer,
    AgentInputSerializer,
    AgentListSerializer,
    ConversationCreateSerializer,
    ConversationListSerializer,
    MessageInputSerializer,
    MessageListSerializer,
    ModelDetectInputSerializer,
    RenameInputSerializer,
)
from .views_toolbox_drf import AgentToolActionsMixin, Conflict

logger = logging.getLogger("ai_assistant")

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


def _conv_pk(request) -> int | None:
    """解析 conversations 路由 pk 为 int；非数字返回 None。"""
    raw = str(request.parser_context["kwargs"]["pk"])
    return int(raw) if raw.isdigit() else None


# ── 模型 API 客户端（health / test / detect 共用）──


def _extract_model_ids(resp_json: dict) -> list:
    """Extract model ID strings from a /models-style API response."""
    if "data" in resp_json:
        return [m.get("id", "") for m in resp_json["data"] if m.get("id")]
    if "models" in resp_json:
        return [m.get("id", "") for m in resp_json["models"] if m.get("id")]
    return []


def call_model_api(agent, path, method="GET", body=None):
    """Call the model provider's API with the agent's credentials."""
    import requests

    api_key = api.decrypt_key(agent.api_key) if agent.api_key else ""
    provider_cfg = get_provider_config(agent.model_provider, agent.base_url)
    base = provider_cfg["base_url"]
    if not base:
        return None, "No base_url configured"
    url = f"{base}{path}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            resp = requests.post(url, headers=headers, json=body or {}, timeout=15)
        return resp, None
    except requests.RequestException as e:
        return None, str(e)


# ═══════════════════════════════════════════════════════════════════
# Agent ViewSet
# ═══════════════════════════════════════════════════════════════════


class AgentViewSet(
    AgentToolActionsMixin,
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

    # ── 列表 ──

    def list(self, request, *args, **kwargs):
        qs = filter_agents_for_user(AIAgent.objects.all(), _user_id(request))
        qs = qs.prefetch_related("tools")
        return Response({"agents": AgentListSerializer(qs, many=True).data})

    # ── 详情 ──

    def retrieve(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        a = AIAgent.objects.prefetch_related("tools").get(id=agent_id)
        return Response({"agent": AgentDetailSerializer(a).data})

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
        agent_id = self._require_owner(request)
        serializer = AgentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = api.update_agent(AIAgent.objects.get(id=agent_id), serializer.validated_data)
        return Response({"id": agent.id})

    # ── 删除 ──

    @action(detail=True, methods=["post"], url_path="delete")
    def delete_agent(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        api.delete_agent(AIAgent.objects.get(id=agent_id))
        return Response({})

    # ── 一次性查看 Key ──

    @action(detail=True, methods=["post"], url_path="reveal-key")
    def reveal_key(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        a = AIAgent.objects.get(id=agent_id)
        try:
            payload = api.reveal_agent_key(a)
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(str(exc))
        return Response(payload)

    # ── 连接测试 ──

    @action(detail=True, methods=["post"], url_path="test")
    def test(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        a = AIAgent.objects.get(id=agent_id)

        available_models = []
        connected = False
        last_error = ""

        for path in _MODEL_LIST_PATHS:
            resp, err = call_model_api(a, path)
            if err:
                last_error = err
                continue
            if resp is not None and 200 <= resp.status_code < 300:
                connected = True
                data = resp.json()
                available_models = _extract_model_ids(data)
                if available_models:
                    cur = a.model_name
                    available_models.sort(key=lambda x: (x != cur, x))
                break
            else:
                last_error = f"HTTP {resp.status_code}"

        if not connected and not last_error:
            chat_body = {
                "model": a.model_name,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5,
            }
            resp, err = call_model_api(a, "/chat/completions", "POST", chat_body)
            if err:
                last_error = err
            elif resp and 200 <= resp.status_code < 300:
                connected = True
            elif resp:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

        api.update_agent_connectivity(
            a,
            connected=connected,
            checked_at=datetime.now(),
            available_models=available_models,
        )
        return Response(
            {
                "connected": connected,
                "available_models": available_models,
                "message": last_error if not connected else "",
            }
        )

    # ── 缓存模型列表（旧 GET /agents/{id}/models；无 owner 校验，保持原行为）──

    @action(detail=True, methods=["get"], url_path="models")
    def models(self, request, *args, **kwargs):
        agent_id = _agent_pk(request)
        if agent_id is None:
            raise NotFound("not found")
        try:
            a = AIAgent.objects.get(id=agent_id)
        except AIAgent.DoesNotExist:
            raise NotFound("not found")
        models = json.loads(a.available_models) if a.available_models else []
        return Response(
            {
                "models": models,
                "is_connected": a.is_connected,
                "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
            }
        )

    # ── 对话（嵌套于 agents/{id}/conversations，Batch 2 迁移）──

    @action(detail=True, methods=["get"], url_path="conversations")
    def list_conversations(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        convs = filter_conversations_for_user(
            AIConversation.objects.filter(agent_id=agent_id),
            _user_id(request),
        ).order_by("-updated_at")
        return Response({"conversations": ConversationListSerializer(convs, many=True).data})

    @action(detail=True, methods=["post"], url_path="conversations/create")
    def create_conversation(self, request, *args, **kwargs):
        agent_id = self._require_owner(request)
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conv = api.create_conversation(
            _user_id(request), agent_id, serializer.validated_data.get("title", "新对话")
        )
        return Response(
            {"id": conv.id, "agent_scope_session_id": conv.agent_scope_session_id or ""}
        )


# ═══════════════════════════════════════════════════════════════════
# 健康检查（独立路由 /agents/health，避免与 /agents/{pk} 冲突）
# ═══════════════════════════════════════════════════════════════════


class AgentHealthAPIView(APIView):
    """GET /api/ai/agents/health — 遍历全部 active Agent（无 owner 过滤，保持原行为）。"""

    def get(self, request):
        from datetime import timedelta

        results = []
        for a in AIAgent.objects.filter(status="active"):
            connected = a.is_connected
            if a.api_key:
                needs_check = not a.last_checked_at or (
                    datetime.now() - a.last_checked_at.replace(tzinfo=None)
                ) > timedelta(minutes=30)
                if needs_check:
                    chat_body = {
                        "model": a.model_name,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 2,
                    }
                    resp, err = call_model_api(a, "/chat/completions", "POST", chat_body)
                    connected = not err and resp is not None and 200 <= resp.status_code < 300
                    api.update_agent_connectivity(a, connected=connected, checked_at=datetime.now())
            results.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "is_connected": connected,
                    "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
                }
            )
        return Response({"agents": results})


# ═══════════════════════════════════════════════════════════════════
# 模型探测（POST 检测 / GET 保持旧 400 语义）
# ═══════════════════════════════════════════════════════════════════


class ModelDetectAPIView(APIView):
    """POST /api/ai/models/detect — 按 provider/base_url/api_key 探测模型列表。"""

    def get(self, request):
        from rest_framework.exceptions import ValidationError

        raise ValidationError("agent_id required")

    def post(self, request):
        serializer = ModelDetectInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = data.get("model_provider", "")
        api_key = data["api_key"]
        provider_cfg = get_provider_config(provider, data.get("base_url", ""))
        base_url = provider_cfg["base_url"]

        import requests

        models = []
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for path in _MODEL_LIST_PATHS:
            try:
                resp = requests.get(f"{base_url.rstrip('/')}{path}", headers=headers, timeout=15)
                if 200 <= resp.status_code < 300:
                    data_json = resp.json()
                    models = _extract_model_ids(data_json)
                    if models:
                        break
            except Exception:
                logger.warning("model detection request failed for %s", base_url)
                continue
        return Response({"models": models})


# ═══════════════════════════════════════════════════════════════════
# 平台工具 / workspace 技能
# ═══════════════════════════════════════════════════════════════════


class AvailableToolsAPIView(APIView):
    """GET /api/ai/available-tools — 平台业务工具（按分类）。"""

    def get(self, request):
        from .agent_scope.tool_registry import TOOL_CATEGORIES, TOOL_SCHEMAS

        tools_by_category = {}
        for t in TOOL_SCHEMAS:
            cat = t.get("category", "其他")
            if cat not in tools_by_category:
                tools_by_category[cat] = []
            tools_by_category[cat].append(
                {
                    "name": t["name"],
                    "summary": t.get("summary", ""),
                    "icon": t.get("icon", ""),
                    "read_only": t.get("read_only", True),
                }
            )

        categories = []
        for c in TOOL_CATEGORIES:
            key = c["key"]
            if key in tools_by_category:
                categories.append(
                    {
                        "key": key,
                        "icon": c["icon"],
                        "color": c["color"],
                        "tools": tools_by_category[key],
                    }
                )
        return Response({"categories": categories})


class AvailableSkillsAPIView(APIView):
    """GET /api/ai/available-skills — workspace 技能列表。"""

    def get(self, request):
        from .agent_scope.skill_registry import _SKILL_CLASS_MAP, ALL_SKILL_NAMES

        skills = []
        for name in ALL_SKILL_NAMES:
            cls = _SKILL_CLASS_MAP.get(name)
            skills.append(
                {
                    "name": name,
                    "description": (cls.description or "").strip() if cls else "",
                }
            )
        return Response({"skills": skills})


# ═══════════════════════════════════════════════════════════════════
# Conversation ViewSet（Batch 2 迁移）— 消息 / 重命名 / 删除 / HITL / 任务
# ═══════════════════════════════════════════════════════════════════


class ConversationViewSet(viewsets.GenericViewSet):
    """对话资源 — 路径与旧 conversation_views/hitl_views 一一对应。

    权限语义与旧实现一致：check_conversation_access 先于存在性检查
    （不存在/无权均 403）；list_conv_tasks/get_conv_task 保持无 owner 校验
    （存量缺口，见方案 D9，不在本迁移修复）。
    """

    queryset = AIConversation.objects.all()

    def _require_access(self, request) -> int:
        conv_id = _conv_pk(request)
        if conv_id is None:
            raise NotFound("conversation not found")
        if not check_conversation_access(_user_id(request), conv_id):
            raise PermissionDenied("Forbidden")
        return conv_id

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, *args, **kwargs):
        conv_id = self._require_access(request)
        msgs = AIMessage.objects.filter(conversation_id=conv_id)
        return Response({"messages": MessageListSerializer(msgs, many=True).data})

    @action(detail=True, methods=["post"], url_path="save-message")
    def save_message(self, request, *args, **kwargs):
        conv_id = self._require_access(request)
        serializer = MessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = data.get("role", "assistant")
        content = data.get("content", "")
        tokens = data.get("tokens", 0)
        blocks = data.get("blocks", [])
        reason = data.get("reason", "normal")
        input_tokens = data.get("input_tokens", 0)
        model_name = data.get("model_name", "")
        flow = data.get("flow", "") or ""
        if flow not in ("", "sse"):
            flow = ""
        blocks_str = json.dumps(blocks) if isinstance(blocks, list) else (blocks or "[]")
        msg = api.save_message(
            conversation_id=conv_id,
            role=role,
            content=content,
            blocks=blocks_str,
            reason=reason,
            tokens=tokens,
            input_tokens=input_tokens,
            model_name=model_name,
            flow=flow,
        )
        return Response({"id": msg.id})

    @action(detail=True, methods=["post"], url_path="rename")
    def rename(self, request, *args, **kwargs):
        conv_id = self._require_access(request)
        serializer = RenameInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conv = api.rename_conversation(
            AIConversation.objects.get(id=conv_id), serializer.validated_data["title"]
        )
        return Response({"title": conv.title})

    @action(detail=True, methods=["post"], url_path="delete")
    def delete(self, request, *args, **kwargs):
        conv_id = self._require_access(request)
        api.delete_conversation(AIConversation.objects.get(id=conv_id))
        return Response({})

    @action(detail=True, methods=["post"], url_path="confirm-result")
    def confirm_result(self, request, *args, **kwargs):
        from .views.hitl_views import deliver_confirm_result

        conv_id = self._require_access(request)
        try:
            conv = AIConversation.objects.get(id=conv_id)
        except AIConversation.DoesNotExist:
            raise NotFound("conversation not found")
        reply_id = request.data.get("reply_id", "")
        confirm_results = request.data.get("confirm_results", [])

        result = deliver_confirm_result(conv_id, reply_id, confirm_results)
        if result is not None:
            status_code, message = result
            if status_code == 409:
                raise Conflict(message)
            from rest_framework.exceptions import ValidationError

            raise ValidationError(message)

        # Log the confirmation（审计写库走 api.py）
        import json as _json

        api.log_confirm_result(
            conv.agent,
            f"User confirm: {_json.dumps(confirm_results, ensure_ascii=False)}",
            _json.dumps({"reply_id": reply_id, "conv_id": conv_id}),
        )
        return Response({})

    @action(detail=True, methods=["get"], url_path="tasks")
    def tasks(self, request, *args, **kwargs):
        conv_id = _conv_pk(request)
        if conv_id is None:
            raise NotFound("conversation not found")
        try:
            AIConversation.objects.get(id=conv_id)
        except AIConversation.DoesNotExist:
            raise NotFound("conversation not found")

        try:
            from django.db.models import Q

            from apps.test_runner.models import TestRunRecord, TestSOP

            # Resolve run_ids linked to this conversation via TestSOP
            sop_run_ids = list(
                TestSOP.objects.filter(conv_id=conv_id)
                .exclude(run_id="")
                .values_list("run_id", flat=True)
            )
            if sop_run_ids:
                qs = TestRunRecord.objects.filter(
                    Q(run_id__startswith="ai-task-", run_id__in=sop_run_ids)
                    | Q(run_id__startswith="case-gen-")
                )
            else:
                qs = TestRunRecord.objects.filter(
                    Q(run_id__startswith="ai-task-") | Q(run_id__startswith="case-gen-")
                )
            tasks = qs.order_by("-id")[:50]
            return Response({"tasks": [_serialize_ai_task(t) for t in tasks]})
        except Exception:
            logger.exception("list_conv_tasks failed")
            from rest_framework.exceptions import APIException

            raise APIException(detail="查询任务历史失败", code=500)

    @action(detail=True, methods=["get"], url_path=r"tasks/(?P<run_id>[^/.]+)")
    def task_detail(self, request, *args, **kwargs):
        run_id = kwargs.get("run_id", "")
        try:
            from apps.test_runner.models import TestRunRecord

            task = TestRunRecord.objects.filter(run_id=run_id).first()
            if not task:
                raise NotFound("task not found")

            return Response(
                {
                    "task": {
                        "run_id": task.run_id,
                        "status": task.status,
                        "device_serial": task.device_serial,
                        "cases": task.selected_cases or [],
                        "loop_count": task.loop_count or 1,
                        "started_at": str(task.started_at) if task.started_at else None,
                        "completed_at": str(task.completed_at)
                        if getattr(task, "completed_at", None)
                        else None,
                        "summary": task.summary or "",
                    }
                }
            )
        except NotFound:
            raise
        except Exception:
            logger.exception("get_conv_task failed for run_id=%s", run_id)
            from rest_framework.exceptions import APIException

            raise APIException(detail="查询任务详情失败", code=500)


# ═══════════════════════════════════════════════════════════════════
# 任务便签看板（GET /api/ai/tasks）
# ═══════════════════════════════════════════════════════════════════


class TaskBoardAPIView(APIView):
    """GET /api/ai/tasks — 工作台任务便签看板（ai-task-* + case-gen-*）。"""

    def get(self, request):
        try:
            from django.db.models import Count, Q

            from apps.test_runner.models import TestRunRecord

            status_q = (request.query_params.get("status") or "all").strip().lower()
            qs = (
                TestRunRecord.objects.filter(
                    Q(run_id__startswith="ai-task-") | Q(run_id__startswith="case-gen-")
                )
                .annotate(
                    total=Count("results"),
                )
                .order_by("-id")
            )

            status_map = {
                "pending": ["PENDING"],
                "running": ["RUNNING"],
                "completed": ["COMPLETED", "SUCCESS"],
                "failed": ["FAILED", "ERROR"],
                "stopped": ["STOPPED", "CANCELLED"],
            }
            if status_q in status_map:
                qs = qs.filter(status__in=status_map[status_q])

            tasks = [_serialize_ai_task(t, total=t.total) for t in qs[:80]]
            return Response({"tasks": tasks})
        except Exception:
            logger.exception("list_ai_tasks failed")
            from rest_framework.exceptions import APIException

            raise APIException(detail="查询 AI 任务列表失败", code=500)


# ── 任务序列化（自 conversation_views 迁入，等行为）──


def _parse_summary(summary):
    if isinstance(summary, dict):
        return summary
    if isinstance(summary, str) and summary.strip():
        try:
            import json as _json

            data = _json.loads(summary)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {"title": summary}
    return {}


def _serialize_ai_task(t, total=0, passed=0):
    meta = _parse_summary(t.summary)
    cases = t.selected_cases or []
    loop = t.loop_count or 1
    progress = meta.get("progress") or {}
    if not isinstance(progress, dict):
        progress = {}
    prog_total = int(progress.get("total") or 0) or max(
        1, (len(cases) if isinstance(cases, list) else 0) * loop
    )
    prog_current = int(total) if total else int(progress.get("current") or 0)
    status = (t.status or "PENDING").upper()
    # Detect task type: case-gen-* = case_generation, ai-task-* = execution
    task_type = meta.get("task_type") or (
        "case_generation" if str(t.run_id).startswith("case-gen-") else "execution"
    )
    return {
        "run_id": t.run_id,
        "title": meta.get("title") or t.run_id,
        "status": status,
        "task_type": task_type,
        "case_type": meta.get("case_type") or "",
        "case_type_label": meta.get("case_type_label") or "",
        "agent_id": str(meta.get("agent_id") or ""),
        "agent_name": meta.get("agent_name") or "未知智能体",
        "device_serial": t.device_serial or "",
        "device_model": meta.get("device_model") or "",
        "cases": cases if isinstance(cases, list) else [],
        "case_titles": meta.get("case_titles") or [],
        "case_ids": meta.get("case_ids") or [],
        "loop_count": loop,
        "progress": {"current": prog_current, "total": prog_total},
        "started_at": str(t.started_at) if t.started_at else None,
        "finished_at": str(t.finished_at) if t.finished_at else None,
    }
