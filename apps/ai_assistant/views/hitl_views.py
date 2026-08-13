"""HITL confirmation endpoint — works with in-process Agent.

The Agent runs in a background thread during SSE streaming. When the frontend
sends a HITL confirmation result, we relay it to the running Agent via a
thread-safe queue stored in the in-memory agent registry.
"""

import asyncio
import json
import logging
import threading

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..decorators import require_auth
from ..models import AIConversation, AIExecutionLog
from ..permissions import check_conversation_access

logger = logging.getLogger("ai_assistant")

# ── In-memory agent session registry ──
# Maps conv_id → asyncio.Queue used to deliver HITL confirm results to the
# running Agent's event loop. The chat_stream view registers the queue when
# streaming starts; send_confirm_result puts results into it.
_agent_sessions: dict[int, dict] = {}
_sessions_lock = threading.Lock()

# Reference to the main event loop (Daphne's loop) for thread-safe queue delivery.
# Set by chat_stream on first use. send_confirm_result (sync view, runs in
# Daphne's thread pool) uses call_soon_threadsafe to safely put into
# the asyncio.Queue from outside the event loop.
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Store the main event loop reference for thread-safe HITL delivery."""
    global _main_loop
    _main_loop = loop


def register_agent_session(conv_id: int, confirm_queue: asyncio.Queue) -> None:
    """Register a running agent session for HITL confirm delivery."""
    with _sessions_lock:
        _agent_sessions[conv_id] = {"confirm_queue": confirm_queue}


def unregister_agent_session(conv_id: int) -> None:
    """Remove a finished agent session."""
    with _sessions_lock:
        _agent_sessions.pop(conv_id, None)


@csrf_exempt
@require_auth
def send_confirm_result(request, conv_id):
    """POST /api/ai/conversations/{id}/confirm-result — relay HITL decision to running Agent."""
    if not check_conversation_access(request.user_id, conv_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        conv = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"status": False, "message": "conversation not found"}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    reply_id = data.get("reply_id", "")
    confirm_results = data.get("confirm_results", [])

    # Try to deliver to running agent (lock held for the entire critical section
    # to prevent the session from being unregistered between lookup and delivery)
    with _sessions_lock:
        session = _agent_sessions.get(conv_id)
        if session is None:
            return JsonResponse(
                {
                    "status": False,
                    "message": "No active agent session — the conversation may have ended or timed out",
                },
                status=400,
            )

        try:
            data = {
                "reply_id": reply_id,
                "confirm_results": confirm_results,
            }
            if _main_loop is not None:
                _main_loop.call_soon_threadsafe(
                    session["confirm_queue"].put_nowait,
                    data,
                )
            else:
                # Fallback for tests or edge cases where main loop is unavailable
                session["confirm_queue"].put_nowait(data)
        except asyncio.QueueFull:
            return JsonResponse(
                {"status": False, "message": "Agent is busy — please try again"},
                status=409,
            )

    # Log the confirmation
    try:
        AIExecutionLog.objects.create(
            agent=conv.agent,
            level="info",
            message=f"User confirm: {json.dumps(confirm_results, ensure_ascii=False)}",
            metadata=json.dumps({"reply_id": reply_id, "conv_id": conv_id}),
        )
    except Exception:
        logger.exception("AIExecutionLog insert failed for conv_id=%s", conv_id)

    return JsonResponse({"status": True})
