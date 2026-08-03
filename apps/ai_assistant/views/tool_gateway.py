"""Tool gateway views — the SINGLE HTTP entry point for AgentScope tool calls.

GET  /api/tools/schemas                    → return all tool definitions (JSON)
GET  /api/tools/agent-config/<agent_id>    → per-agent tool/skill/phase config
POST /api/tools/{module}/{action}           → execute a tool, return result (JSON)

AgentScope calls these endpoints via HTTP (httpx), never via in-process import.
JWT authentication is enforced by the global middleware.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.agent_scope.tool_registry import TOOL_CATEGORIES, TOOL_SCHEMAS, resolve

logger = logging.getLogger("ai_assistant.tools")


@csrf_exempt
def tool_schemas(request):
    """Return all tool schema definitions to AgentScope.

    Called once at AgentScope startup. No authentication required
    (internal service-to-service, Django dev mode passes through).
    """
    return JsonResponse(
        {
            "ok": True,
            "data": {
                "categories": TOOL_CATEGORIES,
                "tools": TOOL_SCHEMAS,
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
    """
    from apps.ai_assistant.models import AIAgent

    agent = None
    # Try Django PK first (int), then AgentScope UUID (str)
    if agent_id.isdigit():
        try:
            agent = AIAgent.objects.prefetch_related("tools").get(id=int(agent_id))
        except AIAgent.DoesNotExist:
            pass
    if agent is None:
        try:
            agent = AIAgent.objects.prefetch_related("tools").get(agent_scope_id=str(agent_id))
        except AIAgent.DoesNotExist:
            return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    # Resolve enabled platform tool names from AITool records
    platform_tools = agent.tools.all()
    platform_names = {t.name for t in platform_tools}
    if platform_names:
        enabled_tools = [t for t in platform_names if t in TOOL_SCHEMAS_BY_NAME]
    else:
        # No configuration → expose all read-only tools as safety fallback
        enabled_tools = [t["name"] for t in TOOL_SCHEMAS if t.get("read_only", True)]

    # Resolve disabled workspace skills
    skills_config = agent.skills_config or {}
    disabled_skills = [name for name, enabled in skills_config.items() if enabled is False]

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
            "ok": True,
            "data": {
                "enabled_tools": enabled_tools,
                "disabled_skills": disabled_skills,
                "knowledge_sources": enabled_sources,
            },
        }
    )


# Pre-build a name→schema lookup for the agent_config view
TOOL_SCHEMAS_BY_NAME = {t["name"]: t for t in TOOL_SCHEMAS}


@csrf_exempt
def tool_gateway(request, module: str, action: str):
    """Execute a business tool on behalf of AgentScope.

    AgentScope POSTs {params} in JSON body. User identity comes from JWT
    (injected by middleware as request.user_id).

    Returns {"ok": True, "data": ...} or {"ok": False, "error": "..."}.
    """
    # ── Resolve handler ──
    handler = resolve(module, action)
    if handler is None:
        return JsonResponse(
            {
                "ok": False,
                "error": f"工具未找到: {module}/{action}",
            },
            status=404,
        )

    # ── Parse body ──
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "error": "无效的 JSON 请求体",
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
                "ok": False,
                "error": str(e),
            },
            status=400,
        )
    except Exception as e:
        logger.exception("Tool %s/%s failed", module, action)
        return JsonResponse(
            {
                "ok": False,
                "error": f"工具执行失败: {e}",
            },
            status=500,
        )

    # ── Serialize ──
    # Django model instances → dict; lists stay as lists; primitive types pass through
    result = _serialize_result(result)

    return JsonResponse(
        {
            "ok": True,
            "data": result,
        }
    )


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
    # Django model instance
    if hasattr(obj, "_meta"):
        return _model_to_dict(obj)
    # Fallback
    return str(obj)


def _model_to_dict(instance) -> dict:
    """Convert a single Django model instance to dict."""
    data = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname, None)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        data[field.attname] = value
    # Include @property and cached relations
    if hasattr(instance, "page") and hasattr(instance, "_page_cache"):
        pass  # already handled via select_related
    return data
