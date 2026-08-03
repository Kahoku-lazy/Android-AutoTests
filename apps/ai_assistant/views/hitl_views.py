"""HITL & AgentScope session endpoints."""

import hashlib
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.agent_scope.provider_registry import get_provider_config

logger = logging.getLogger("ai_assistant")

from ..api import decrypt_key
from ..decorators import require_auth
from ..models import AIConversation, AIExecutionLog
from ..permissions import check_conversation_access
from .agent_views import _do_register_agentscope_agent
from .common import call_agentscope, create_agentscope_credential, get_agentscope_token


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
    reply_id = data.get("reply_id", "")
    confirm_results = data.get("confirm_results", [])

    token = get_agentscope_token(request)
    resp, err = call_agentscope(
        f"/sessions/{conv.agent_scope_session_id}/confirm",
        "POST",
        {"reply_id": reply_id, "confirm_results": confirm_results},
        token,
        timeout=10,
    )

    if err:
        return JsonResponse(
            {"ok": False, "error": f"confirm result send failed: {err}"}, status=503
        )

    try:
        AIExecutionLog.objects.create(
            agent=conv.agent,
            level="info",
            message=f"User confirm: {json.dumps(confirm_results, ensure_ascii=False)}",
            metadata=json.dumps({"reply_id": reply_id, "conv_id": conv_id}),
        )
    except Exception:
        logger.exception("AIExecutionLog insert failed for conv_id=%s", conv_id)

    return JsonResponse({"ok": True})


@csrf_exempt
@require_auth
def create_scope_session(request, conv_id):
    """POST /api/ai/conversations/{id}/create-scope-session — Create AgentScope SSE session."""
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        conv = AIConversation.objects.select_related("agent").get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    if conv.agent_scope_session_id:
        # If agent was updated after this conversation was created, the API key
        # stored in the AgentScope credential may be stale. Re-create the session
        # with a fresh credential to avoid 401 authentication errors.
        if conv.agent.updated_at <= conv.created_at:
            return JsonResponse(
                {
                    "ok": True,
                    "session_id": conv.agent_scope_session_id,
                    "agent_scope_id": conv.agent.agent_scope_id,
                }
            )
        # Agent was updated — fall through to create a new credential + session

    api_key = decrypt_key(conv.agent.api_key) if conv.agent.api_key else ""
    if not api_key:
        return JsonResponse(
            {"ok": False, "error": "Agent has no API key — cannot create session"}, status=400
        )

    if not conv.agent.agent_scope_id:
        token = get_agentscope_token(request)
        agent_scope_id, err = _do_register_agentscope_agent(conv.agent, token)
        if err:
            return JsonResponse(
                {"ok": False, "error": f"Agent registration failed: {err}"},
                status=503,
            )
        conv.agent.refresh_from_db()

    agent_scope_id = conv.agent.agent_scope_id
    provider_cfg = get_provider_config(conv.agent.model_provider, conv.agent.base_url)

    token = get_agentscope_token(request)

    # Reuse existing AgentScope credential if the API key / base_url haven't changed.
    cred_key = f"{api_key}|{provider_cfg['base_url']}|{provider_cfg['credential_type']}"
    cred_hash = hashlib.sha256(cred_key.encode()).hexdigest()
    agent_model = conv.agent
    if agent_model.agent_scope_credential_id and agent_model.credential_hash == cred_hash:
        credential_id = agent_model.agent_scope_credential_id
    else:
        credential_id, cred_err = create_agentscope_credential(
            provider_cfg, api_key, str(conv.agent.id), token
        )
        if cred_err:
            return JsonResponse({"ok": False, "error": cred_err}, status=503)
        agent_model.agent_scope_credential_id = credential_id
        agent_model.credential_hash = cred_hash
        agent_model.save(update_fields=["agent_scope_credential_id", "credential_hash"])

    # Build model parameters, merging generate_kwargs from agent config
    agent_model = conv.agent
    parameters = {
        "temperature": agent_model.temperature or 0.7,
        "max_tokens": agent_model.max_tokens or 4096,
    }
    generate_kwargs_str = (agent_model.generate_kwargs or "{}").strip()
    if generate_kwargs_str and generate_kwargs_str != "{}":
        try:
            extra = json.loads(generate_kwargs_str)
            if isinstance(extra, dict):
                parameters.update(extra)
        except (json.JSONDecodeError, TypeError):
            pass

    session_body = {
        "agent_id": agent_scope_id,
        "chat_model_config": {
            "type": provider_cfg["credential_type"],
            "credential_id": credential_id,
            "model": agent_model.model_name,
            "parameters": parameters,
        },
    }

    # AgentScope stores registrations in memory. If the service was restarted,
    # the agent_id / credential_id stored in Django are stale → 404.
    # Re-register and retry once automatically.
    for attempt in (1, 2):
        resp, err = call_agentscope("/sessions/", "POST", session_body, token)
        if resp is not None and resp.status_code == 404 and attempt == 1:
            logger.warning(
                "AgentScope session 404 for agent %s — re-registering after restart",
                conv.agent.id,
            )
            # Clear stale registration IDs
            agent_model.agent_scope_id = ""
            agent_model.agent_scope_credential_id = ""
            agent_model.credential_hash = ""
            agent_model.save(
                update_fields=[
                    "agent_scope_id",
                    "agent_scope_credential_id",
                    "credential_hash",
                ]
            )

            # Re-register agent
            agent_scope_id, reg_err = _do_register_agentscope_agent(
                agent_model,
                token,
            )
            if reg_err:
                return JsonResponse(
                    {"ok": False, "error": f"Agent re-registration failed: {reg_err}"},
                    status=503,
                )

            # Re-create credential
            credential_id, cred_err = create_agentscope_credential(
                provider_cfg,
                api_key,
                str(agent_model.id),
                token,
            )
            if cred_err:
                return JsonResponse(
                    {"ok": False, "error": cred_err},
                    status=503,
                )
            agent_model.agent_scope_credential_id = credential_id
            agent_model.credential_hash = cred_hash
            agent_model.save(
                update_fields=[
                    "agent_scope_credential_id",
                    "credential_hash",
                ]
            )

            # Retry with fresh IDs
            session_body["agent_id"] = agent_scope_id
            session_body["chat_model_config"]["credential_id"] = credential_id
            continue

        if err:
            return JsonResponse(
                {"ok": False, "error": f"session creation failed: {err}"},
                status=503,
            )
        if resp.status_code not in (200, 201):
            return JsonResponse(
                {
                    "ok": False,
                    "error": f"session creation failed: HTTP {resp.status_code} — {resp.text[:200]}",
                },
                status=503,
            )
        break  # Success

    session_id = resp.json().get("session_id", "")
    conv.agent_scope_session_id = session_id
    conv.save(update_fields=["agent_scope_session_id", "updated_at"])

    return JsonResponse(
        {
            "ok": True,
            "session_id": session_id,
            "agent_scope_id": agent_scope_id,
        }
    )
