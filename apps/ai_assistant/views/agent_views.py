"""Agent CRUD, reveal-key, health check, AgentScope registration."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from agentscope_service.provider_registry import get_provider_config

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
from .common import call_agentscope, get_agentscope_token, validation_error


def list_agents(request):
    qs = filter_agents_for_user(AIAgent.objects.all(), getattr(request, 'user_id', None))
    agents = []
    for a in qs.prefetch_related('tools'):
        tool_count = sum(1 for t in a.tools.all() if t.enabled)
        agents.append({
            "id": a.id, "name": a.name, "avatar": a.avatar, "tags": a.tags,
            "description": a.description, "model_provider": a.model_provider,
            "model_name": a.model_name, "status": a.status,
            "tool_count": tool_count,
            "created_at": str(a.created_at),
        })
    return JsonResponse({"ok": True, "agents": agents})


def agent_detail(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.prefetch_related('tools').get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)
    tools = [{"id": t.id, "name": t.name, "tool_type": t.tool_type,
              "config_json": t.config_json, "enabled": t.enabled} for t in a.tools.all()]
    return JsonResponse({"ok": True, "agent": {
        "id": a.id, "name": a.name, "avatar": a.avatar, "tags": a.tags,
        "description": a.description, "model_provider": a.model_provider,
        "model_name": a.model_name,
        "api_key": mask_key(decrypt_key(a.api_key) if a.api_key else ''),
        "base_url": a.base_url,
        "system_prompt": a.system_prompt, "temperature": a.temperature,
        "max_tokens": a.max_tokens, "formatter": a.formatter,
        "max_iters": a.max_iters, "parallel_tool_calls": a.parallel_tool_calls,
        "print_hint_msg": a.print_hint_msg, "memory_mode": a.memory_mode,
        "long_term_memory_mode": a.long_term_memory_mode,
        "enable_meta_tool": a.enable_meta_tool,
        "enable_rewrite_query": a.enable_rewrite_query,
        "generate_kwargs": a.generate_kwargs,
        "compression_enabled": a.compression_enabled,
        "compression_threshold": a.compression_threshold,
        "compression_keep_recent": a.compression_keep_recent,
        "compression_prompt": a.compression_prompt,
        "compression_template": a.compression_template,
        "tts_enabled": a.tts_enabled, "status": a.status,
        "tools": tools,
        "is_connected": a.is_connected,
        "last_checked_at": str(a.last_checked_at) if a.last_checked_at else None,
        "available_models": json.loads(a.available_models) if a.available_models else [],
        "created_at": str(a.created_at),
    }})


@csrf_exempt
@require_auth
def create_agent(request):
    if not check_can_create_agent(request.user_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = json.loads(request.body)
    ok, errors, cleaned = validate_agent_input(data, require_api_key=True)
    if not ok:
        return validation_error(errors)
    data = cleaned
    a = AIAgent.objects.create(
        owner_id=int(request.user_id),
        name=data.get("name", ""), avatar=data.get("avatar", "🤖"),
        tags=data.get("tags", ""), description=data.get("description", ""),
        model_provider=data.get("model_provider", "dashscope"),
        model_name=data.get("model_name", "qwen-max"),
        api_key=encrypt_key(data.get("api_key", "")), base_url=data.get("base_url", ""),
        system_prompt=data.get("system_prompt", ""),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 4096),
        formatter=data.get("formatter", "dashscope"),
        max_iters=data.get("max_iters", 10),
        parallel_tool_calls=data.get("parallel_tool_calls", False),
        print_hint_msg=data.get("print_hint_msg", False),
        memory_mode=data.get("memory_mode", "inmemory"),
        long_term_memory_mode=data.get("long_term_memory_mode", "both"),
        enable_meta_tool=data.get("enable_meta_tool", False),
        enable_rewrite_query=data.get("enable_rewrite_query", True),
        generate_kwargs=data.get("generate_kwargs", "{}"),
        compression_enabled=data.get("compression_enabled", False),
        compression_threshold=data.get("compression_threshold", 10000),
        compression_keep_recent=data.get("compression_keep_recent", 3),
        compression_prompt=data.get("compression_prompt", ""),
        compression_template=data.get("compression_template", ""),
        tts_enabled=data.get("tts_enabled", False),
        key_revealed=False)
    for t in data.get("tools", []):
        AITool.objects.create(agent=a, name=t.get("name", ""),
            tool_type=t.get("tool_type", "mcp"),
            config_json=t.get("config_json", "{}"), enabled=t.get("enabled", True))
    return JsonResponse({"ok": True, "id": a.id})


@csrf_exempt
@require_auth
def update_agent(request, agent_id):
    if not check_can_update_agent(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)
    data = json.loads(request.body)
    ok, errors, cleaned = validate_agent_input(data, require_api_key=False)
    if not ok:
        return validation_error(errors)
    data = cleaned
    key_changed = False
    if 'api_key' in data and data['api_key']:
        if '***' in data['api_key']:
            del data['api_key']
        else:
            data['api_key'] = encrypt_key(data['api_key'])
            key_changed = True
    for f in ['name', 'avatar', 'tags', 'description', 'model_provider', 'model_name',
              'api_key', 'base_url', 'system_prompt', 'temperature', 'max_tokens',
              'formatter', 'max_iters', 'parallel_tool_calls', 'print_hint_msg',
              'memory_mode', 'long_term_memory_mode', 'enable_meta_tool',
              'enable_rewrite_query', 'generate_kwargs',
              'compression_enabled', 'compression_threshold', 'compression_keep_recent',
              'compression_prompt', 'compression_template', 'tts_enabled', 'status']:
        if f in data:
            setattr(a, f, data[f])
    if key_changed:
        a.key_revealed = False
    a.save()
    if 'tools' in data:
        a.tools.all().delete()
        for t in data['tools']:
            AITool.objects.create(agent=a, name=t.get("name", ""),
                tool_type=t.get("tool_type", "mcp"),
                config_json=t.get("config_json", "{}"), enabled=t.get("enabled", True))
    return JsonResponse({"ok": True})


@csrf_exempt
@require_auth
def reveal_api_key(request, agent_id):
    """POST /api/ai/agents/<id>/reveal-key — one-time decrypted API key reveal."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    if not a.api_key:
        return JsonResponse({"ok": False, "error": "未配置 API Key"}, status=400)

    if a.key_revealed:
        decrypted = decrypt_key(a.api_key)
        return JsonResponse({
            "ok": True,
            "api_key": mask_key(decrypted),
            "revealed": False,
            "hint": "API Key 仅支持一次性查看，已过期",
        })

    decrypted = decrypt_key(a.api_key)
    a.key_revealed = True
    a.save(update_fields=['key_revealed', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "api_key": decrypted,
        "revealed": True,
        "hint": "请立即复制保存，此 Key 仅显示一次",
    })


@csrf_exempt
@require_auth
def delete_agent(request, agent_id):
    if not check_can_delete_agent(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    AIAgent.objects.filter(id=agent_id).delete()
    return JsonResponse({"ok": True})


def health_check_all_agents(request):
    """GET /api/ai/agents/health — check connectivity of all active agents."""
    from datetime import datetime, timedelta
    from .model_views import call_model_api

    results = []
    for a in AIAgent.objects.filter(status="active"):
        connected = a.is_connected
        if a.api_key:
            needs_check = (
                not a.last_checked_at
                or (datetime.now() - a.last_checked_at.replace(tzinfo=None)) > timedelta(minutes=30)
            )
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

        results.append({
            "id": a.id,
            "name": a.name,
            "is_connected": connected,
            "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
        })
    return JsonResponse({"ok": True, "agents": results})


@csrf_exempt
@require_auth
def register_agent_in_agentscope(request, agent_id):
    """POST /api/ai/agents/{id}/register-scope — Register Django agent with AgentScope."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        agent_cfg = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    api_key = decrypt_key(agent_cfg.api_key) if agent_cfg.api_key else ''
    if not api_key:
        return JsonResponse({"ok": False, "error": "API key required for AgentScope registration"}, status=400)

    token = get_agentscope_token(request)
    provider_cfg = get_provider_config(agent_cfg.model_provider, agent_cfg.base_url)

    credential_body = {
        "data": {
            "type": provider_cfg["credential_type"],
            "api_key": api_key,
            "base_url": provider_cfg["base_url"],
            "agent_django_id": str(agent_id),
        },
    }

    resp, err = call_agentscope('/credential/', 'POST', credential_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"credential creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"credential creation failed: HTTP {resp.status_code} — {resp.text[:200]}"}, status=503)

    credential_id = resp.json().get('credential_id', '')

    agent_body = {
        "name": agent_cfg.name,
        "system_prompt": agent_cfg.system_prompt or "你是一个有用的AI测试助手。",
        "react_config": {
            "max_iters": agent_cfg.max_iters or 10,
            "parallel_tool_calls": agent_cfg.parallel_tool_calls,
        },
    }
    resp, err = call_agentscope('/agent/', 'POST', agent_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"agent creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"agent creation failed: HTTP {resp.status_code} — {resp.text[:200]}"}, status=503)

    agent_scope_id = resp.json().get('agent_id', '')
    if not agent_scope_id:
        return JsonResponse({"ok": False, "error": "AgentScope did not return agent_id"}, status=503)

    agent_cfg.agent_scope_id = agent_scope_id
    agent_cfg.save(update_fields=['agent_scope_id', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "agent_scope_id": agent_scope_id,
        "credential_id": credential_id,
    })
