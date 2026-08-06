"""SSE streaming chat views — Agent runs directly in Django process.

Replaces the old dual-request flow:
  1. POST /api/ai/conversations/{id}/create-scope-session (Django → AgentScope HTTP)
  2. GET /agentscope/sessions/{id}/stream (SSE from AgentScope)
  3. POST /agentscope/chat/ (trigger AgentScope)

With a single request:
  POST /api/ai/conversations/{id}/chat/stream
  → Django builds Agent in-process → streams reply events as SSE → saves result
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.agent_scope.agent_factory import build_agent
from apps.ai_assistant.api import save_message
from apps.ai_assistant.models import AIConversation

from ..decorators import require_auth
from ..permissions import check_conversation_access

logger = logging.getLogger("ai_assistant.chat")


@csrf_exempt
@require_auth
def chat_stream(request, conv_id):
    """POST /api/ai/conversations/{conv_id}/chat/stream

    Request body: {"message": "user text"}
    Response: text/event-stream (SSE)

    The single request replaces the old create-scope-session + subscribe + trigger flow.
    Agent is built in-process from AIAgent config and reply events are streamed
    directly to the frontend.
    """
    # ── Auth & load ──
    if not check_conversation_access(request.user_id, conv_id):
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)

    try:
        conv = AIConversation.objects.select_related("agent").get(id=conv_id)
    except AIConversation.DoesNotExist:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "conversation not found"}, status=404)

    # ── Parse message ──
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    user_message = body.get("message", "").strip()
    if not user_message:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "消息不能为空"}, status=400)

    user_id_str = str(request.user_id) if request.user_id else ""

    # ── Save user message to DB ──
    try:
        save_message(
            conversation_id=conv_id,
            role="user",
            content=user_message,
            flow="sse",
        )
    except Exception:
        logger.exception("Failed to save user message for conv=%s", conv_id)

    # ── Bridge async AgentScope to sync Django ──
    # AgentScope Agent is fully async. We bridge it to Django's sync view
    # using a dedicated event loop in a background thread + a queue.

    result_queue: queue.Queue = queue.Queue()

    def _run_agent():
        """Run the async agent in a background thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_agent_stream(conv, user_id_str, user_message, result_queue))
        except Exception:
            logger.exception("Agent stream failed for conv=%s", conv_id)
            result_queue.put(None)  # sentinel
        finally:
            loop.close()

    thread = threading.Thread(target=_run_agent, daemon=True)
    thread.start()

    # ── SSE event generator (sync, consumed by StreamingHttpResponse) ──

    def event_generator():
        while True:
            try:
                chunk = result_queue.get(timeout=120)  # 2-min max between events
            except queue.Empty:
                # Timeout — agent may be stuck, send heartbeat comment
                yield ": heartbeat\n\n"
                continue

            if chunk is None:  # sentinel — agent finished or crashed
                break

            yield chunk

    response = StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
    # Prevent Django from buffering the entire response
    response._is_rendered = True
    return response


# ═══════════════════════════════════════════════════════════════════════
# Async core — runs in background thread with own event loop
# ═══════════════════════════════════════════════════════════════════════


async def _agent_stream(
    conv: AIConversation,
    user_id: str,
    user_message: str,
    queue: queue.Queue,
) -> None:
    """Build agent, restore context, stream reply events to queue.

    All AgentScope interactions happen here — model calls, tool execution,
    streaming. Events are pushed to the sync queue for the SSE generator.
    """
    from agentscope.message import UserMsg

    agent_model = conv.agent

    # ── 1. Build agent ──
    agent = build_agent(
        agent_model=agent_model,
        user_id=user_id,
        conversation_id=conv.id,
    )

    # ── 2. Restore conversation context from DB ──
    from asgiref.sync import sync_to_async

    await sync_to_async(_restore_context)(agent, conv)

    # ── 3. Register for HITL confirmations ──
    from .hitl_views import register_agent_session, unregister_agent_session

    confirm_queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    register_agent_session(conv.id, confirm_queue)

    try:
        # ── 4. Stream reply ──
        from agentscope.event import (
            ExceedMaxItersEvent,
            ReplyEndEvent,
            RequireUserConfirmEvent,
            UserConfirmResultEvent,
        )

        next_input = UserMsg(name=user_id, content=user_message)

        while True:
            async for event in agent.reply_stream(next_input):
                json_str = event.model_dump_json()
                queue.put(f"data: {json_str}\n\n")

                # If agent requires user confirmation, wait for it via the queue
                if isinstance(event, RequireUserConfirmEvent):
                    try:
                        # Wait for frontend to send confirm result (via send_confirm_result)
                        confirm_data = await asyncio.wait_for(
                            confirm_queue.get(),
                            timeout=120.0,  # 2-minute timeout for user to respond
                        )
                    except asyncio.TimeoutError:
                        logger.warning("HITL confirm timeout for conv=%s", conv.id)
                        break

                    # Build UserConfirmResultEvent and continue the loop

                    confirm_items = []
                    for cr in confirm_data.get("confirm_results", []):
                        tc = cr.get("tool_call", {})
                        confirmed = cr.get("approved", cr.get("confirmed", False))
                        confirm_items.append(
                            {
                                "tool_call": {
                                    "id": cr.get("tool_call_id", ""),
                                    "name": tc.get("name", ""),
                                    "input": tc.get("input", "{}"),
                                },
                                "confirmed": confirmed,
                            }
                        )

                    next_input = UserConfirmResultEvent(
                        reply_id=confirm_data.get("reply_id", ""),
                        confirm_results=confirm_items,
                    )
                    continue  # Continue the reply loop with confirm result

                # Terminal events — exit the loop
                if isinstance(event, (ReplyEndEvent, ExceedMaxItersEvent)):
                    break

            break  # Exit outer while if inner loop completed naturally

    except Exception:
        logger.exception("Agent reply_stream failed for conv=%s", conv.id)
        error_event = json.dumps(
            {
                "type": "TEXT_BLOCK_DELTA",
                "block_id": "error",
                "delta": "\n\n[Agent 执行异常，请重试]",
            }
        )
        queue.put(f"data: {error_event}\n\n")
    finally:
        unregister_agent_session(conv.id)

    # ── Sentinel ──
    queue.put(None)


def _restore_context(agent, conv: AIConversation) -> None:
    """Restore agent conversation context from saved AIMessage records.

    Loads messages from DB and feeds them into agent.state.context so the
    Agent has full conversation history.

    IMPORTANT: Called from the sync thread (via _run_agent), not from
    the async _agent_stream, to avoid SynchronousOnlyOperation.
    """
    from agentscope.message import AssistantMsg, UserMsg

    messages = list(conv.messages.order_by("created_at"))
    for msg in messages:
        if msg.role == "user":
            agent.state.context.append(
                UserMsg(name="user", content=msg.content),
            )
        elif msg.role == "assistant":
            # Restore blocks if available, otherwise fall back to plain text
            try:
                blocks_data = json.loads(msg.blocks) if msg.blocks else []
            except (json.JSONDecodeError, TypeError):
                blocks_data = []

            if blocks_data:
                # Convert stored block dicts to AgentScope content blocks
                content_blocks = _dicts_to_blocks(blocks_data)
                agent.state.context.append(
                    AssistantMsg(
                        name=agent.name,
                        content=content_blocks,
                    )
                )
            else:
                agent.state.context.append(
                    AssistantMsg(
                        name=agent.name,
                        content=msg.content or "",
                    ),
                )

    logger.debug(
        "Restored %d messages for agent '%s' conv=%s",
        len(messages),
        agent.name,
        conv.id,
    )


def _dicts_to_blocks(blocks_data: list[dict]) -> list:
    """Convert stored block dicts to AgentScope block objects."""
    from agentscope.message import (
        DataBlock,
        HintBlock,
        TextBlock,
        ThinkingBlock,
        ToolCallBlock,
        ToolResultBlock,
    )

    _BLOCK_CLASS_MAP = {
        "text": TextBlock,
        "thinking": ThinkingBlock,
        "tool_call": ToolCallBlock,
        "tool_result": ToolResultBlock,
        "hint": HintBlock,
        "data": DataBlock,
    }

    blocks = []
    for b in blocks_data:
        block_type = b.get("type", "")
        cls = _BLOCK_CLASS_MAP.get(block_type)
        if cls:
            try:
                # Filter to only valid kwargs for each block class
                valid_fields = {
                    "text",
                    "thinking",
                    "name",
                    "input",
                    "output",
                    "id",
                    "state",
                    "hint",
                    "source",
                    "media_type",
                }
                kwargs = {k: v for k, v in b.items() if k in valid_fields and k != "type"}
                blocks.append(cls(**kwargs))
            except Exception:
                # Fallback: wrap as text
                blocks.append(TextBlock(text=str(b.get("text", b.get("output", "")))))
    return blocks
