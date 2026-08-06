"""Conversation & message endpoints."""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
)
from .common import validation_error

logger = logging.getLogger("ai_assistant")


@require_auth
def list_conversations(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    convs = filter_conversations_for_user(
        AIConversation.objects.filter(agent_id=agent_id),
        getattr(request, "user_id", None),
    ).order_by("-updated_at")
    return JsonResponse(
        {
            "status": True,
            "conversations": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "agent_scope_session_id": c.agent_scope_session_id or "",
                    "created_at": str(c.created_at),
                }
                for c in convs
            ],
        }
    )


@csrf_exempt
@require_auth
def create_conversation(request, agent_id):
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    data = json.loads(request.body)
    ok, errors, cleaned = validate_conversation_input(data)
    if not ok:
        return validation_error(errors)
    c = AIConversation.objects.create(
        owner_id=int(request.user_id),
        agent_id=agent_id,
        title=cleaned.get("title", "新对话"),
    )
    return JsonResponse(
        {"status": True, "id": c.id, "agent_scope_session_id": c.agent_scope_session_id or ""}
    )


@csrf_exempt
@require_auth
def delete_conversation(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)
    c.delete()
    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def rename_conversation(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"status": False, "message": "conversation not found"}, status=404)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse(
            {"status": False, "message": "invalid request encoding, use UTF-8"}, status=400
        )
    ok, errors, cleaned = validate_rename_input(data)
    if not ok:
        return validation_error(errors)
    c.title = cleaned["title"]
    c.save()
    return JsonResponse({"status": True, "title": c.title})


@require_auth
def list_messages(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    msgs = AIMessage.objects.filter(conversation_id=conv_id)
    return JsonResponse(
        {
            "status": True,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "blocks": json.loads(m.blocks) if m.blocks else [],
                    "reason": m.reason or "normal",
                    "tool_calls": m.tool_calls,
                    "tokens": m.tokens,
                    "input_tokens": m.input_tokens or 0,
                    "model_name": m.model_name or "",
                    "flow": m.flow or "",
                    "created_at": str(m.created_at),
                }
                for m in msgs
            ],
        }
    )


@csrf_exempt
@require_auth
def save_message(request, conv_id):
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    data = json.loads(request.body)
    ok, errors, _ = validate_message_input(data)
    if not ok:
        return validation_error(errors)
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
    msg = AIMessage.objects.create(
        conversation_id=conv_id,
        role=role,
        content=content,
        tokens=tokens,
        blocks=json.dumps(blocks) if isinstance(blocks, list) else (blocks or "[]"),
        reason=reason,
        input_tokens=input_tokens,
        model_name=model_name,
        flow=flow,
    )
    return JsonResponse({"status": True, "id": msg.id})


@require_auth
def list_conv_tasks(request, conv_id):
    try:
        AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"status": False, "message": "conversation not found"}, status=404)

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

        return JsonResponse({"status": True, "tasks": [_serialize_ai_task(t) for t in tasks]})
    except Exception:
        logger.exception("list_conv_tasks failed")
        return JsonResponse({"status": False, "message": "查询任务历史失败"}, status=500)


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
        return JsonResponse({"status": True, "tasks": tasks})
    except Exception:
        logger.exception("list_ai_tasks failed")
        return JsonResponse({"status": False, "message": "查询 AI 任务列表失败"}, status=500)


@require_auth
def get_conv_task(request, conv_id, run_id):
    try:
        from apps.test_runner.models import TestRunRecord

        task = TestRunRecord.objects.filter(run_id=run_id).first()
        if not task:
            return JsonResponse({"status": False, "message": "task not found"}, status=404)

        return JsonResponse(
            {
                "status": True,
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
                },
            }
        )
    except Exception:
        logger.exception("get_conv_task failed for run_id=%s", run_id)
        return JsonResponse({"status": False, "message": "查询任务详情失败"}, status=500)
