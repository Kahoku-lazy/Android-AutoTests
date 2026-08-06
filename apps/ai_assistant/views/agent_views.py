"""Agent CRUD, reveal-key, health check, AgentScope registration."""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("ai_assistant")

from ..api import decrypt_key, encrypt_key, mask_key
from ..decorators import require_auth
from ..models import AIAgent, AITool
from ..permissions import (
    check_agent_owner,
    check_can_create_agent,
    check_can_delete_agent,
    check_can_update_agent,
    filter_agents_for_user,
)
from ..serializers import validate_agent_input
from .common import validation_error


def list_available_skills(request):
    """GET /api/ai/available-skills — return workspace skills that can be toggled."""
    from apps.ai_assistant.agent_scope.skill_registry import _SKILL_CLASS_MAP, ALL_SKILL_NAMES

    skills = []
    for name in ALL_SKILL_NAMES:
        cls = _SKILL_CLASS_MAP.get(name)
        skills.append(
            {
                "name": name,
                "description": (cls.description or "").strip() if cls else "",
            }
        )
    return JsonResponse({"status": True, "skills": skills})


def list_agents(request):
    qs = filter_agents_for_user(AIAgent.objects.all(), getattr(request, "user_id", None))
    agents = []
    for a in qs.prefetch_related("tools"):
        tool_count = sum(1 for t in a.tools.all() if t.enabled)
        agents.append(
            {
                "id": a.id,
                "name": a.name,
                "avatar": a.avatar,
                "tags": a.tags,
                "description": a.description,
                "model_provider": a.model_provider,
                "model_name": a.model_name,
                "status": a.status,
                "tool_count": tool_count,
                "created_at": str(a.created_at),
            }
        )
    return JsonResponse({"status": True, "agents": agents})


@require_auth
def agent_detail(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.prefetch_related("tools").get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    tools = [
        {
            "id": t.id,
            "name": t.name,
            "tool_type": t.tool_type,
            "config_json": t.config_json,
            "enabled": t.enabled,
        }
        for t in a.tools.all()
    ]
    return JsonResponse(
        {
            "status": True,
            "agent": {
                "id": a.id,
                "name": a.name,
                "avatar": a.avatar,
                "tags": a.tags,
                "description": a.description,
                "model_provider": a.model_provider,
                "model_name": a.model_name,
                "api_key": mask_key(decrypt_key(a.api_key) if a.api_key else ""),
                "base_url": a.base_url,
                "system_prompt": a.system_prompt,
                "temperature": a.temperature,
                "max_tokens": a.max_tokens,
                "formatter": a.formatter,
                "max_iters": a.max_iters,
                "parallel_tool_calls": a.parallel_tool_calls,
                "print_hint_msg": a.print_hint_msg,
                "memory_mode": a.memory_mode,
                "long_term_memory_mode": a.long_term_memory_mode,
                "enable_meta_tool": a.enable_meta_tool,
                "enable_rewrite_query": a.enable_rewrite_query,
                "enable_knowledge_base": a.enable_knowledge_base,
                "enable_workspace_tools": a.enable_workspace_tools,
                "enable_business_tools": a.enable_business_tools,
                "enable_mcp_tools": a.enable_mcp_tools,
                "enable_skills": a.enable_skills,
                "generate_kwargs": a.generate_kwargs,
                "skills_config": a.skills_config or {},
                "knowledge_sources": a.knowledge_sources or {},
                "compression_enabled": a.compression_enabled,
                "compression_threshold": a.compression_threshold,
                "compression_keep_recent": a.compression_keep_recent,
                "compression_prompt": a.compression_prompt,
                "compression_template": a.compression_template,
                "tts_enabled": a.tts_enabled,
                "status": a.status,
                "tools": tools,
                "is_connected": a.is_connected,
                "last_checked_at": str(a.last_checked_at) if a.last_checked_at else None,
                "available_models": json.loads(a.available_models) if a.available_models else [],
                "created_at": str(a.created_at),
            },
        }
    )


@csrf_exempt
@require_auth
def create_agent(request):
    if not check_can_create_agent(request.user_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)
    ok, errors, cleaned = validate_agent_input(data, require_api_key=False)
    if not ok:
        return validation_error(errors)
    data = cleaned
    # Agents start as pure conversation models — no default system prompt.
    a = AIAgent.objects.create(
        owner_id=int(request.user_id),
        name=data.get("name", ""),
        avatar=data.get("avatar", "🤖"),
        tags=data.get("tags", ""),
        description=data.get("description", ""),
        model_provider=data.get("model_provider", "dashscope"),
        model_name=data.get("model_name", "qwen-max"),
        api_key=encrypt_key(data.get("api_key", "")),
        base_url=data.get("base_url", ""),
        system_prompt=data.get("system_prompt", ""),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 4096),
        formatter=data.get("formatter", "dashscope"),
        max_iters=data.get("max_iters", 10),
        parallel_tool_calls=data.get("parallel_tool_calls", True),
        print_hint_msg=data.get("print_hint_msg", False),
        memory_mode=data.get("memory_mode", "inmemory"),
        long_term_memory_mode=data.get("long_term_memory_mode", "both"),
        enable_meta_tool=data.get("enable_meta_tool", False),
        enable_rewrite_query=data.get("enable_rewrite_query", True),
        enable_knowledge_base=data.get("enable_knowledge_base", False),
        enable_workspace_tools=data.get("enable_workspace_tools", False),
        enable_business_tools=data.get("enable_business_tools", False),
        enable_mcp_tools=data.get("enable_mcp_tools", False),
        enable_skills=data.get("enable_skills", False),
        generate_kwargs=data.get("generate_kwargs", "{}"),
        compression_enabled=data.get("compression_enabled", False),
        compression_threshold=data.get("compression_threshold", 10000),
        compression_keep_recent=data.get("compression_keep_recent", 3),
        compression_prompt=data.get("compression_prompt", ""),
        compression_template=data.get("compression_template", ""),
        tts_enabled=data.get("tts_enabled", False),
        skills_config=data.get("skills_config", {}),
        knowledge_sources=data.get("knowledge_sources", {}),
        key_revealed=False,
    )
    for t in data.get("tools", []):
        AITool.objects.create(
            agent=a,
            name=t.get("name", ""),
            tool_type=t.get("tool_type", "mcp"),
            config_json=t.get("config_json", "{}"),
            enabled=t.get("enabled", True),
        )
    return JsonResponse({"status": True, "id": a.id})


def _sync_agent_tools(agent, tools_data):
    """Diff-based tool sync: add new, update changed, remove deleted.

    Avoids the DELETE-ALL + INSERT-ALL anti-pattern — only touches
    rows that actually changed, preserving primary keys."""
    existing = {t.name: t for t in agent.tools.all()}
    incoming = {}
    for t in tools_data:
        name = (t.get("name") or "").strip()
        if not name:
            continue
        incoming[name] = t

    # Delete removed tools
    for name, existing_tool in existing.items():
        if name not in incoming:
            existing_tool.delete()

    # Create new / update existing
    for name, tool_data in incoming.items():
        if name in existing:
            et = existing[name]
            new_config = tool_data.get("config_json", "{}")
            new_type = tool_data.get("tool_type", "mcp")
            new_enabled = tool_data.get("enabled", True)
            if (
                et.config_json != new_config
                or et.tool_type != new_type
                or et.enabled != new_enabled
            ):
                et.config_json = new_config
                et.tool_type = new_type
                et.enabled = new_enabled
                et.save()
        else:
            AITool.objects.create(
                agent=agent,
                name=name,
                tool_type=tool_data.get("tool_type", "mcp"),
                config_json=tool_data.get("config_json", "{}"),
                enabled=tool_data.get("enabled", True),
            )


@csrf_exempt
@require_auth
def update_agent(request, agent_id):
    if not check_can_update_agent(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)
    ok, errors, cleaned = validate_agent_input(data, require_api_key=False)
    if not ok:
        return validation_error(errors)
    data = cleaned
    key_changed = False
    prompt_changed = False
    provider_changed = False
    if "api_key" in data and data["api_key"]:
        # Frontend sends masked value (contains "***") when key is unchanged
        if "***" in data["api_key"]:
            del data["api_key"]
        else:
            data["api_key"] = encrypt_key(data["api_key"])
            key_changed = True
    # Detect provider/base_url changes so we can sync credentials
    if ("model_provider" in data and str(data["model_provider"]) != str(a.model_provider)) or (
        "base_url" in data and str(data["base_url"]).rstrip("/") != str(a.base_url).rstrip("/")
    ):
        provider_changed = True
    for f in [
        "name",
        "avatar",
        "tags",
        "description",
        "model_provider",
        "model_name",
        "api_key",
        "base_url",
        "system_prompt",
        "temperature",
        "max_tokens",
        "formatter",
        "max_iters",
        "parallel_tool_calls",
        "print_hint_msg",
        "memory_mode",
        "long_term_memory_mode",
        "enable_meta_tool",
        "enable_rewrite_query",
        "enable_knowledge_base",
        "enable_workspace_tools",
        "enable_business_tools",
        "enable_mcp_tools",
        "enable_skills",
        "generate_kwargs",
        "compression_enabled",
        "compression_threshold",
        "compression_keep_recent",
        "compression_prompt",
        "compression_template",
        "tts_enabled",
        "status",
        "skills_config",
        "knowledge_sources",
    ]:
        if f in data:
            if f == "system_prompt" and str(getattr(a, f, "")) != str(data[f]):
                prompt_changed = True
            setattr(a, f, data[f])
    if key_changed:
        a.key_revealed = False
    # When system_prompt changes, clear agent_scope_id so it gets
    # re-registered with the new prompt on the next session creation.
    if prompt_changed and a.agent_scope_id:
        a.agent_scope_id = ""
    a.save()
    if "tools" in data:
        _sync_agent_tools(a, data["tools"])

    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def reveal_api_key(request, agent_id):
    """POST /api/ai/agents/<id>/reveal-key — one-time decrypted API key reveal."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)

    if not a.api_key:
        return JsonResponse({"status": False, "message": "未配置 API Key"}, status=400)

    if a.key_revealed:
        decrypted = decrypt_key(a.api_key)
        return JsonResponse(
            {
                "status": True,
                "api_key": mask_key(decrypted),
                "revealed": False,
                "hint": "API Key 仅支持一次性查看，已过期",
            }
        )

    decrypted = decrypt_key(a.api_key)
    a.key_revealed = True
    a.save(update_fields=["key_revealed", "updated_at"])

    return JsonResponse(
        {
            "status": True,
            "api_key": decrypted,
            "revealed": True,
            "hint": "请立即复制保存，此 Key 仅显示一次",
        }
    )


@csrf_exempt
@require_auth
def delete_agent(request, agent_id):
    if not check_can_delete_agent(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    AIAgent.objects.filter(id=agent_id).delete()
    return JsonResponse({"status": True})


@require_auth
def health_check_all_agents(request):
    """GET /api/ai/agents/health — check connectivity of all active agents."""
    from datetime import datetime, timedelta

    from .model_views import call_model_api

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
                a.is_connected = connected
                a.last_checked_at = datetime.now()
                a.save()

        results.append(
            {
                "id": a.id,
                "name": a.name,
                "is_connected": connected,
                "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
            }
        )
    return JsonResponse({"status": True, "agents": results})
