"""Conversation & message endpoints."""
import json
import logging

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

logger = logging.getLogger('ai_assistant')


def _check_agentscope_available():
    """Check if AgentScope service is reachable.

    Returns (True, None) or (False, error_message).
    """
    import urllib.request
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/docs', method='HEAD')
        urllib.request.urlopen(req, timeout=2)
        return True, None
    except Exception as e:
        return False, str(e)


def _check_redis_available():
    """Check if Redis is reachable.

    Returns (True, None) or (False, error_message).
    """
    try:
        from config.agentscope_config import check_redis_connection
        return check_redis_connection()
    except Exception as e:
        return False, str(e)


def health_check(request):
    """GET /api/ai/health — 平台健康检查（无需认证）。

    Returns:
        {
            "ok": true,
            "redis_available": bool,
            "agentscope_available": bool,
            "mode": "full" | "degraded" | "offline"
        }

    mode:
      - "full":     Redis + AgentScope 都正常，SSE 流式对话可用
      - "degraded": Redis 或 AgentScope 不可用，AI 对话降级为 Django 直调模式
      - "offline":  两者都不可用
    """
    redis_ok, _ = _check_redis_available()
    agentscope_ok, _ = _check_agentscope_available()

    if redis_ok and agentscope_ok:
        mode = 'full'
    elif not redis_ok and not agentscope_ok:
        mode = 'offline'
    else:
        mode = 'degraded'

    return JsonResponse({
        'ok': True,
        'redis_available': redis_ok,
        'agentscope_available': agentscope_ok,
        'mode': mode,
    })


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
         "flow": m.flow or '',
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

    AIMessage.objects.create(
        conversation=conv, role=role, content=response_text, tokens=tokens, flow="fallback",
    )
    conv.title = user_text[:30] if conv.title == "新对话" else conv.title
    conv.save(update_fields=["title", "updated_at"])

    agentscope_ok, _ = _check_agentscope_available()
    return JsonResponse({
        "ok": True,
        "message": {"role": role, "content": response_text, "tokens": tokens, "flow": "fallback"},
        "degraded": not agentscope_ok,
    })


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
    flow = data.get('flow', '') or ''
    if flow not in ('', 'sse', 'fallback'):
        flow = ''
    msg = AIMessage.objects.create(
        conversation_id=conv_id,
        role=role,
        content=content,
        tokens=tokens,
        blocks=json.dumps(blocks) if isinstance(blocks, list) else (blocks or '[]'),
        reason=reason,
        input_tokens=input_tokens,
        model_name=model_name,
        flow=flow,
    )
    return JsonResponse({"ok": True, "id": msg.id})


@csrf_exempt
@require_auth
def stream_chat(request, conv_id):
    """POST /api/ai/conversations/{id}/stream — Django-native SSE streaming.

    Calls the AI model API directly with stream=True and relays chunks as
    SSE events.  Does NOT require AgentScope or Redis — works in degraded mode.
    """
    from django.http import StreamingHttpResponse

    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    try:
        conv = AIConversation.objects.select_related('agent').get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    data = json.loads(request.body)
    user_text = data.get('message', '').strip()
    if not user_text:
        return JsonResponse({"ok": False, "error": "message required"}, status=400)

    # Save user message
    AIMessage.objects.create(conversation=conv, role="user", content=user_text)

    agent_cfg = conv.agent
    api_key = decrypt_key(agent_cfg.api_key) if agent_cfg.api_key else ''
    provider = agent_cfg.model_provider
    model_name = agent_cfg.model_name
    system_prompt = agent_cfg.system_prompt or "你是一个有用的AI助手。"
    base_url = (get_provider_config(provider, agent_cfg.base_url) or {}).get("base_url", "")

    if not api_key:
        return JsonResponse({"ok": False, "error": "Agent 未配置 API Key"}, status=400)

    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    history = AIMessage.objects.filter(conversation=conv).order_by('-created_at')[:20]
    for m in reversed(list(history)):
        if m.role in ('user', 'assistant'):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_text})

    def generate():
        full_text = []
        try:
            if provider == "dashscope":
                url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                body = {"model": model_name, "messages": messages, "stream": True}
                if agent_cfg.temperature:
                    body["temperature"] = float(agent_cfg.temperature)
            else:
                url = f"{base_url.rstrip('/')}/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                body = {"model": model_name, "messages": messages, "stream": True}
                if agent_cfg.temperature:
                    body["temperature"] = float(agent_cfg.temperature)

            import requests as req
            resp = req.post(url, headers=headers, json=body, stream=True, timeout=120)
            if resp.status_code != 200:
                yield f'data: {{"type":"error","error":"API error {resp.status_code}: {resp.text[:200]}"}}\n\n'
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]  # strip "data: " prefix
                if data_str == "[DONE]":
                    yield f'data: {{"type":"done"}}\n\n'
                    continue
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_text.append(content)
                        escaped = json.dumps({"type": "delta", "content": content})
                        yield f"data: {escaped}\n\n"
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
        except Exception as e:
            yield f'data: {{"type":"error","error":"{str(e)}"}}\n\n'

        # Save assistant message after stream completes
        final = "".join(full_text)
        if final.strip():
            AIMessage.objects.create(
                conversation=conv, role="assistant", content=final,
                tokens=len(final), model_name=model_name, flow="sse",
            )

    response = StreamingHttpResponse(
        generate(), content_type='text/event-stream', status=200,
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


def list_conv_tasks(request, conv_id):
    try:
        AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    try:
        from django.db.models import Q
        from apps.test_runner.models import TestRunRecord, TestSOP
        # Resolve run_ids linked to this conversation via TestSOP
        sop_run_ids = list(
            TestSOP.objects.filter(conv_id=conv_id)
            .exclude(run_id="")
            .values_list("run_id", flat=True)
        )
        # ai-task-* records are scoped to conversation via TestSOP.
        # case-gen-* records (from CreateCaseGenTaskTool) are not linked
        # through TestSOP — include them unconditionally for this conversation.
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

        return JsonResponse({"ok": True, "tasks": [
            _serialize_ai_task(t) for t in tasks
        ]})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def _parse_summary(summary):
    if isinstance(summary, dict):
        return summary
    if isinstance(summary, str) and summary.strip():
        try:
            import json
            data = json.loads(summary)
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
    prog_total = int(progress.get("total") or 0) or max(1, (len(cases) if isinstance(cases, list) else 0) * loop)
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


@csrf_exempt
@require_auth
def list_ai_tasks(request):
    """GET /api/ai/tasks — 工作台任务便签看板（ai-task-* + case-gen-*）。

    Query: status=all|pending|running|completed|failed|stopped
    """
    try:
        from django.db.models import Count, Q
        from apps.test_runner.models import TestRunRecord

        status_q = (request.GET.get("status") or "all").strip().lower()
        qs = TestRunRecord.objects.filter(
            Q(run_id__startswith="ai-task-") | Q(run_id__startswith="case-gen-")
        ).annotate(
            total=Count("results"),
        ).order_by("-id")

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
        return JsonResponse({"ok": True, "tasks": tasks})
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
