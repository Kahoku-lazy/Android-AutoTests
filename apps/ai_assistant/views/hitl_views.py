"""HITL & AgentScope session endpoints."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from agentscope_service.provider_registry import get_provider_config

from ..api import decrypt_key
from ..decorators import require_auth
from ..models import AIConversation, AIExecutionLog
from ..permissions import check_conversation_access
from .agent_views import register_agent_in_agentscope
from .common import call_agentscope, get_agentscope_token


@csrf_exempt
@require_auth
def send_confirm_result(request, conv_id):
    """POST /api/ai/conversations/{id}/confirm-result — relay HITL decision to AgentScope."""
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        conv = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    if not conv.agent_scope_session_id:
        return JsonResponse({"ok": False, "error": "no AgentScope session"}, status=400)

    data = json.loads(request.body)
    reply_id = data.get('reply_id', '')
    confirm_results = data.get('confirm_results', [])

    token = get_agentscope_token(request)
    resp, err = call_agentscope(
        f"/sessions/{conv.agent_scope_session_id}/confirm",
        'POST',
        {"reply_id": reply_id, "confirm_results": confirm_results},
        token,
        timeout=10,
    )

    if err:
        return JsonResponse({"ok": False, "error": f"confirm result send failed: {err}"}, status=503)

    try:
        AIExecutionLog.objects.create(
            agent=conv.agent,
            level='info',
            message=f"User confirm: {json.dumps(confirm_results, ensure_ascii=False)}",
            metadata=json.dumps({"reply_id": reply_id, "conv_id": conv_id}),
        )
    except Exception:
        pass

    return JsonResponse({"ok": True})


@csrf_exempt
@require_auth
def create_scope_session(request, conv_id):
    """POST /api/ai/conversations/{id}/create-scope-session — Create AgentScope SSE session."""
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        conv = AIConversation.objects.select_related('agent').get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    if conv.agent_scope_session_id:
        return JsonResponse({
            "ok": True,
            "session_id": conv.agent_scope_session_id,
            "agent_scope_id": conv.agent.agent_scope_id,
        })

    api_key = decrypt_key(conv.agent.api_key) if conv.agent.api_key else ''
    if not api_key:
        return JsonResponse({"ok": False, "error": "Agent has no API key — cannot create session"}, status=400)

    if not conv.agent.agent_scope_id:
        reg_resp_data = register_agent_in_agentscope(request, conv.agent.id)
        reg_body = json.loads(reg_resp_data.content)
        if not reg_body.get('ok'):
            return JsonResponse({
                "ok": False,
                "error": f"Agent registration failed: {reg_body.get('error', 'unknown')}",
            }, status=503)
        conv.agent.refresh_from_db()

    agent_scope_id = conv.agent.agent_scope_id
    provider_cfg = get_provider_config(conv.agent.model_provider, conv.agent.base_url)

    token = get_agentscope_token(request)
    credential_resp, err = call_agentscope('/credential/', 'POST', {
        "data": {
            "type": provider_cfg["credential_type"],
            "api_key": api_key,
            "base_url": provider_cfg["base_url"],
            "agent_django_id": str(conv.agent.id),
        },
    }, token)
    if err or credential_resp.status_code not in (200, 201):
        return JsonResponse({
            "ok": False,
            "error": f"credential creation failed: {err or credential_resp.text[:200]}",
        }, status=503)
    credential_id = credential_resp.json().get('credential_id', '')

    session_body = {
        "agent_id": agent_scope_id,
        "chat_model_config": {
            "type": provider_cfg["credential_type"],
            "credential_id": credential_id,
            "model": conv.agent.model_name,
            "parameters": {
                "temperature": conv.agent.temperature or 0.7,
                "max_tokens": conv.agent.max_tokens or 4096,
            },
        },
    }
    resp, err = call_agentscope('/sessions/', 'POST', session_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"session creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({
            "ok": False,
            "error": f"session creation failed: HTTP {resp.status_code} — {resp.text[:200]}",
        }, status=503)

    session_id = resp.json().get('session_id', '')
    conv.agent_scope_session_id = session_id
    conv.save(update_fields=['agent_scope_session_id', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "session_id": session_id,
        "agent_scope_id": agent_scope_id,
    })
