"""Tool gateway views — HTTP 工具入口（工具执行 / schemas / agent-config）。

GET  /api/ai/tools/schemas                  → return all tool definitions (JSON)
GET  /api/ai/tools/agent-config/<agent_id>  → per-agent tool/skill/phase config
POST /api/ai/tools/<module>/<action>        → execute a tool, return result (JSON)

工具实现真相源：`apps/ai_assistant/tools.py`（`TOOLS` + `TOOL_META`）；本网关 handler 亦 resolve 到该处。
本网关为 HTTP 工具入口（历史/外部调用方）；AgentScope 已并入进程内，正常链路不经此网关。

鉴权：该前缀在 JWT 中间件中豁免（服务间调用不持有用户令牌），由
`gateway.internal_token.InternalToolTokenMiddleware` 校验请求头 `X-Internal-Token`；
令牌（`settings.AI_TOOL_GATEWAY_TOKEN`）未配置时一律 401。
"""

import json
import logging

from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.tools import (
    TOOL_CATEGORIES,
    list_tool_schemas,
    resolve_by_module_action,
)

logger = logging.getLogger("ai_assistant.tools")


@csrf_exempt
def tool_schemas(request):
    """Return all tool schema definitions (服务间调用).

    Requires the internal token header (`X-Internal-Token`); JWT is exempt for this prefix.
    """
    return JsonResponse(
        {
            "status": True,
            "data": {
                "categories": TOOL_CATEGORIES,
                "tools": list_tool_schemas(),
            },
        }
    )


@csrf_exempt
def agent_config(request, agent_id: str):
    """GET /api/tools/agent-config/<agent_id> — per-agent tool/skill/phase config.

    Returns:
      - enabled_tools: list of tool names the agent can use
      - disabled_skills: list of workspace skill names to hide
      - knowledge_sources: list of document IDs for RAG filtering
      - capability_flags: dict of enable_* boolean toggles
    """
    from apps.ai_assistant.models import AIAgent

    agent = None
    # Try Django PK first (int), then AgentScope UUID (str)
    if agent_id.isdigit():
        try:
            agent = AIAgent.objects.get(id=int(agent_id))
        except AIAgent.DoesNotExist:
            # 预期未命中：先按 Django PK 查，落空后继续按 AgentScope UUID 查
            pass
    if agent is None:
        try:
            agent = AIAgent.objects.get(agent_scope_id=str(agent_id))
        except AIAgent.DoesNotExist:
            return JsonResponse({"status": False, "message": "agent not found"}, status=404)

    # Resolve enabled platform tool names from the global switchboard (AI 工具箱)
    from apps.ai_assistant.api import get_platform_tool_enabled_map

    enabled_tools = [name for name, on in get_platform_tool_enabled_map().items() if on]

    # If business tools are disabled at the capability level, clear them
    if not agent.enable_business_tools:
        enabled_tools = []

    # Resolve disabled workspace skills
    skills_config = agent.skills_config or {}
    disabled_skills = [name for name, enabled in skills_config.items() if enabled is False]

    # workspace 技能已移除，恒为空
    if not agent.enable_workspace_tools:
        disabled_skills = []

    # Resolve enabled knowledge sources (dict → list of enabled IDs)
    sources_raw = agent.knowledge_sources or {}
    if isinstance(sources_raw, dict):
        enabled_sources = [k for k, v in sources_raw.items() if v is True]
    elif isinstance(sources_raw, list):
        # Legacy list format: [] = all, ["__none__"] = none
        if not sources_raw or sources_raw == ["__none__"]:
            enabled_sources = []
        else:
            enabled_sources = [s for s in sources_raw if s != "__none__"]
    else:
        enabled_sources = []

    return JsonResponse(
        {
            "status": True,
            "data": {
                "enabled_tools": enabled_tools,
                "disabled_skills": disabled_skills,
                "knowledge_sources": enabled_sources,
                "capability_flags": {
                    "enable_workspace_tools": agent.enable_workspace_tools,
                    "enable_business_tools": agent.enable_business_tools,
                    "enable_mcp_tools": agent.enable_mcp_tools,
                    "enable_skills": agent.enable_skills,
                    "enable_knowledge_base": agent.enable_knowledge_base,
                },
            },
        }
    )


@csrf_exempt
def tool_gateway(request, module: str, action: str):
    """Execute a business tool on behalf of a service caller.

    Requires the internal token header (`X-Internal-Token`); JWT is exempt for this prefix.
    The caller POSTs {params} in the JSON body. `request.user_id` is only present when the
    caller also sends a JWT — service callers have no user identity, so it falls back to "".

    Returns {"status": True, "data": ...} or {"status": False, "message": "..."}.
    """
    # ── Resolve handler ──
    handler = resolve_by_module_action(module, action)
    if handler is None:
        return JsonResponse(
            {
                "status": False,
                "message": f"工具未找到: {module}/{action}",
            },
            status=404,
        )

    # ── Parse body ──
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": False,
                "message": "无效的 JSON 请求体",
            },
            status=400,
        )

    # ── Inject user_id from JWT middleware ──
    user_id = str(getattr(request, "user_id", "") or "")

    # ── Execute ──
    try:
        result = handler(user_id=user_id, **body)
    except ValueError as e:
        return JsonResponse(
            {
                "status": False,
                "message": str(e),
            },
            status=400,
        )
    except Exception as e:
        logger.exception("Tool %s/%s failed", module, action)
        return JsonResponse(
            {
                "status": False,
                "message": f"工具执行失败: {e}",
            },
            status=500,
        )

    # ── Serialize ──
    # Django model instances → dict; lists stay as lists; primitive types pass through
    result = _serialize_result(_normalize_tool_result(result))

    return JsonResponse(
        {
            "status": True,
            "data": result,
        }
    )


def _normalize_tool_result(result):
    """新 tools.py 函数返回 str(JSON) 或 ToolChunk，统一成 dict/list/str。"""
    from agentscope.tool import ToolChunk

    if isinstance(result, ToolChunk):
        text = "".join(getattr(b, "text", "") for b in result.content)
        try:
            return json.loads(text) if text else ""
        except (json.JSONDecodeError, TypeError):
            return text
    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result
    return result


def _serialize_result(obj):
    """Convert ORM objects to dicts for JSON serialization."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialize_result(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_result(item) for item in obj]
    # Django QuerySet (lazy — must evaluate before serializing)
    if isinstance(obj, QuerySet):
        return [_model_to_dict(item) for item in obj]
    # Django model instance
    if hasattr(obj, "_meta"):
        return _model_to_dict(obj)
    # Fallback — avoid passing QuerySet repr strings to the LLM
    return str(obj)


def _model_to_dict(instance) -> dict:
    """Convert a single Django model instance to dict."""
    data = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname, None)
        if value is not None and hasattr(value, "isoformat"):
            value = value.isoformat()
        data[field.attname] = value
    # Include @property and cached relations
    if hasattr(instance, "page") and hasattr(instance, "_page_cache"):
        pass  # already handled via select_related
    return data
