"""Conversation & message endpoints."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from agentscope_service.provider_registry import get_provider_config

from ..api import decrypt_key
from ..decorators import require_auth
from ..models import AIConversation, AIMessage
from ..permissions import (
    check_agent_owner,
    check_conversation_access,
    filter_conversations_for_user,
)
from ..serializers import (
    validate_conversation_input,
    validate_message_input,
    validate_rename_input,
    validate_send_message_input,
)
from .common import validation_error


def list_conversations(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    convs = filter_conversations_for_user(
        AIConversation.objects.filter(agent_id=agent_id),
        getattr(request, 'user_id', None),
    ).order_by('-updated_at')
    return JsonResponse({"ok": True, "conversations": [
        {"id": c.id, "title": c.title, "status": c.status,
         "agent_scope_session_id": c.agent_scope_session_id or '',
         "created_at": str(c.created_at)} for c in convs]})


@csrf_exempt
@require_auth
def create_conversation(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = json.loads(request.body)
    ok, errors, cleaned = validate_conversation_input(data)
    if not ok:
        return validation_error(errors)
    c = AIConversation.objects.create(
        owner_id=int(request.user_id),
        agent_id=agent_id,
        title=cleaned.get("title", "新对话"),
    )
    return JsonResponse({"ok": True, "id": c.id, "agent_scope_session_id": c.agent_scope_session_id or ''})


@csrf_exempt
@require_auth
def delete_conversation(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)
    c.delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_auth
def rename_conversation(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "invalid request encoding, use UTF-8"}, status=400)
    ok, errors, cleaned = validate_rename_input(data)
    if not ok:
        return validation_error(errors)
    c.title = cleaned["title"]
    c.save()
    return JsonResponse({"ok": True, "title": c.title})


def list_messages(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    msgs = AIMessage.objects.filter(conversation_id=conv_id)
    return JsonResponse({"ok": True, "messages": [
        {"id": m.id, "role": m.role, "content": m.content,
         "blocks": json.loads(m.blocks) if m.blocks else [],
         "reason": m.reason or 'normal',
         "tool_calls": m.tool_calls,
         "tokens": m.tokens,
         "input_tokens": m.input_tokens or 0,
         "model_name": m.model_name or '',
         "created_at": str(m.created_at)} for m in msgs]})


@csrf_exempt
@require_auth
def send_message(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        conv = AIConversation.objects.select_related('agent').get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    data = json.loads(request.body)
    ok, errors, cleaned = validate_send_message_input(data)
    if not ok:
        return validation_error(errors)
    user_text = cleaned["message"]

    AIMessage.objects.create(conversation=conv, role="user", content=user_text)

    agent_cfg = conv.agent
    response_text = ""
    tokens = 0
    try:
        response_text, tokens = _run_agent(agent_cfg, user_text, conv)
        role = "assistant"
    except Exception as e:
        response_text = f"抱歉，智能体运行出错：{str(e)}"
        role = "assistant"

    AIMessage.objects.create(conversation=conv, role=role, content=response_text, tokens=tokens)
    conv.title = user_text[:30] if conv.title == "新对话" else conv.title
    conv.save(update_fields=["title", "updated_at"])

    return JsonResponse({"ok": True, "message": {"role": role, "content": response_text, "tokens": tokens}})


def _run_agent(agent_cfg, user_text, conv) -> tuple:
    provider = agent_cfg.model_provider
    model_name = agent_cfg.model_name
    api_key = decrypt_key(agent_cfg.api_key) if agent_cfg.api_key else ''
    provider_cfg = get_provider_config(provider, agent_cfg.base_url)
    base_url = provider_cfg["base_url"]
    system_prompt = agent_cfg.system_prompt
    temperature = agent_cfg.temperature

    if not api_key:
        return "请先配置 API Key", 0

    messages = [{"role": "system", "content": system_prompt or "你是一个有用的AI助手。"}]
    history = AIMessage.objects.filter(conversation=conv).order_by('-created_at')[:20]
    for m in reversed(list(history)):
        if m.role in ('user', 'assistant'):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_text})

    try:
        if provider == "dashscope":
            return _call_dashscope(messages, api_key, model_name, temperature)
        return _call_openai(messages, api_key, model_name, base_url, temperature)
    except Exception as e:
        return f"调用模型失败：{str(e)}", 0


def _call_dashscope(messages, api_key, model_name, temperature):
    import requests
    resp = requests.post(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": messages, "temperature": temperature},
        timeout=120,
    )
    if resp.status_code == 200:
        body = resp.json()
        choice = body["choices"][0]
        return choice["message"]["content"], body.get("usage", {}).get("total_tokens", 0)
    return f"API 错误 ({resp.status_code}): {resp.text[:200]}", 0


def _call_openai(messages, api_key, model_name, base_url, temperature):
    import requests
    url = f"{base_url.rstrip('/')}/chat/completions"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": messages, "temperature": temperature},
        timeout=120,
    )
    if resp.status_code == 200:
        body = resp.json()
        choice = body["choices"][0]
        return choice["message"]["content"], body.get("usage", {}).get("total_tokens", 0)
    return f"API 错误 ({resp.status_code}): {resp.text[:200]}", 0


@csrf_exempt
@require_auth
def save_message(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = json.loads(request.body)
    ok, errors, _ = validate_message_input(data)
    if not ok:
        return validation_error(errors)
    role = data.get('role', 'assistant')
    content = data.get('content', '')
    tokens = data.get('tokens', 0)
    blocks = data.get('blocks', [])
    reason = data.get('reason', 'normal')
    input_tokens = data.get('input_tokens', 0)
    model_name = data.get('model_name', '')
    msg = AIMessage.objects.create(
        conversation_id=conv_id,
        role=role,
        content=content,
        tokens=tokens,
        blocks=json.dumps(blocks) if isinstance(blocks, list) else (blocks or '[]'),
        reason=reason,
        input_tokens=input_tokens,
        model_name=model_name,
    )
    return JsonResponse({"ok": True, "id": msg.id})


@csrf_exempt
@require_auth
def stream_chat(request, conv_id):
    return JsonResponse({"ok": False, "error": "streaming not yet available — use /send for now"}, status=501)


def list_conv_tasks(request, conv_id):
    try:
        AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    try:
        from apps.test_runner.models import TestRunRecord
        tasks = TestRunRecord.objects.filter(
            run_id__startswith="ai-task-"
        ).order_by("-started_at")[:50]

        return JsonResponse({"ok": True, "tasks": [
            {
                "run_id": t.run_id,
                "status": t.status,
                "device_serial": t.device_serial,
                "device_model": "",
                "cases": t.selected_cases or [],
                "loop_count": t.loop_count or 1,
                "started_at": str(t.started_at) if t.started_at else None,
                "completed_at": str(t.completed_at) if getattr(t, 'completed_at', None) else None,
                "summary": t.summary or "",
            }
            for t in tasks
        ]})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def get_conv_task(request, conv_id, run_id):
    try:
        from apps.test_runner.models import TestRunRecord
        task = TestRunRecord.objects.filter(run_id=run_id).first()
        if not task:
            return JsonResponse({"ok": False, "error": "task not found"}, status=404)

        return JsonResponse({"ok": True, "task": {
            "run_id": task.run_id,
            "status": task.status,
            "device_serial": task.device_serial,
            "cases": task.selected_cases or [],
            "loop_count": task.loop_count or 1,
            "started_at": str(task.started_at) if task.started_at else None,
            "completed_at": str(task.completed_at) if getattr(task, 'completed_at', None) else None,
            "summary": task.summary or "",
        }})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
