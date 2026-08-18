"""SSE streaming chat views — Agent runs directly in Django process.

Replaces the old dual-request flow:
  1. POST /api/ai/conversations/{id}/create-scope-session (Django → AgentScope HTTP)
  2. GET /agentscope/sessions/{id}/stream (SSE from AgentScope)
  3. POST /agentscope/chat/ (trigger AgentScope)

With a single request:
  POST /api/ai/conversations/{id}/chat/stream
  → Django builds Agent in-process → streams reply events as SSE → saves result

Architecture: async Django view running directly in Daphne's event loop.
AgentScope's async reply_stream is consumed directly — no background thread,
no sync queue.Queue bridge. Each await/yield returns control to the event
loop so Daphne can flush TCP chunks between SSE events, producing true
token-by-token streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from asgiref.sync import sync_to_async as _original_sta
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.agent_scope.agent_factory import build_agent
from apps.ai_assistant.api import save_message
from apps.ai_assistant.models import AIConversation

from ..decorators import require_auth
from ..permissions import check_conversation_access

logger = logging.getLogger("ai_assistant.chat")


# ── Background agent task tracking ──
# Hold references to asyncio.Tasks so they are not GC'd and exceptions are
# not silently swallowed. Same pattern as test_runner.views.helpers._spawn_bg.
_bg_agent_tasks: set[asyncio.Task] = set()

# Track the active agent task per conversation so we can cancel a stale task
# when a new request arrives for the same conv_id before the old one finishes.
_active_agent_tasks: dict[int, asyncio.Task] = {}


def _sta(fn):
    """sync_to_async with thread_sensitive=False.

    Uses a generic thread pool instead of the request-scoped
    CurrentThreadExecutor, so DB operations (save_message, build_agent, etc.)
    continue to work after the HTTP response has been sent / client disconnected.
    """
    return _original_sta(fn, thread_sensitive=False)


@csrf_exempt
@require_auth
async def chat_stream(request, conv_id):
    """POST /api/ai/conversations/{conv_id}/chat/stream

    Request body: {"message": "user text"}
    Response: text/event-stream (SSE)

    Async Django view — runs directly in Daphne's event loop.  AgentScope's
    async reply_stream is consumed via an asyncio.Queue + async generator,
    eliminating the old threading.Thread + queue.Queue bridge.

    Each yield of an SSE chunk returns control to the event loop, letting
    Daphne flush the TCP buffer — producing true token-by-token streaming.
    """
    # ── Auth & load ──
    if not await _sta(check_conversation_access)(request.user_id, conv_id):
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)

    try:
        conv = await _sta(AIConversation.objects.select_related("agent").get)(id=conv_id)
    except AIConversation.DoesNotExist:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "conversation not found"}, status=404)

    # ── Parse message ──
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    user_message = (body.get("message") or "").strip()
    raw_images = body.get("images") or []
    if not isinstance(raw_images, list):
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "images 必须是数组"}, status=400)

    images, img_err = _normalize_images(raw_images)
    if img_err:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": img_err}, status=400)

    if not user_message and not images:
        from django.http import JsonResponse

        return JsonResponse({"status": False, "message": "消息不能为空"}, status=400)

    display_text = (body.get("display_text") or "").strip()
    content_for_db = display_text or user_message or ("[图片]" if images else "")
    user_blocks = _build_user_blocks(user_message, images)

    user_id_str = str(request.user_id) if request.user_id else ""

    # ── Save user message to DB ──
    try:
        await _sta(save_message)(
            conversation_id=conv_id,
            role="user",
            content=content_for_db,
            blocks=json.dumps(user_blocks, ensure_ascii=False) if user_blocks else "",
            flow="sse",
        )
    except Exception:
        logger.exception("Failed to save user message for conv=%s", conv_id)

    # ── Store the main event loop for HITL thread-safe delivery ──
    from .hitl_views import set_main_loop

    set_main_loop(asyncio.get_running_loop())

    # ── Cache the loop for test_runner cross-thread dispatch (AI run_test tool) ──
    from apps.test_runner.api import set_main_loop as set_test_runner_loop

    set_test_runner_loop(asyncio.get_running_loop())

    # ── asyncio.Queue replaces the old sync queue.Queue ──
    result_queue: asyncio.Queue = asyncio.Queue()

    # Cancel any stale agent task for the same conversation (e.g. from a
    # prior SSE request that the browser abandoned without aborting).
    old_task = _active_agent_tasks.get(int(conv_id))
    if old_task and not old_task.done():
        old_task.cancel()
        logger.debug("Cancelled stale agent task for conv=%s", conv_id)

    # Fire-and-forget: Agent runs as a Task in the same event loop.
    # Holds a reference in _bg_agent_tasks so the Task is not GC'd and
    # exceptions are surfaced (same pattern as test_runner._spawn_bg).
    agent_task = asyncio.create_task(
        _agent_stream(conv, user_id_str, user_message, images, result_queue),
    )
    _bg_agent_tasks.add(agent_task)
    _active_agent_tasks[int(conv_id)] = agent_task
    agent_task.add_done_callback(_bg_agent_tasks.discard)
    agent_task.add_done_callback(
        lambda _: _active_agent_tasks.pop(int(conv_id), None),
    )

    # ── Async SSE event generator (consumed by StreamingHttpResponse) ──

    async def event_generator():
        while True:
            try:
                chunk = await asyncio.wait_for(result_queue.get(), timeout=120)
            except asyncio.TimeoutError:
                # No events for 2 min — agent may be stuck, send heartbeat
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
            "Content-Encoding": "identity",
        },
    )
    # Prevent Django from buffering the entire response
    response._is_rendered = True
    return response


# ═══════════════════════════════════════════════════════════════════════
# Async core — runs as an asyncio.Task in Daphne's main event loop
# ═══════════════════════════════════════════════════════════════════════


async def _agent_stream(
    conv: AIConversation,
    user_id: str,
    user_message: str,
    images: list[dict],
    queue: asyncio.Queue,
) -> None:
    """Build agent, restore context, stream reply events to queue.

    All AgentScope interactions happen here — model calls, tool execution,
    streaming. Events are pushed to the asyncio.Queue for the SSE generator.
    """
    from agentscope.message import Base64Source, DataBlock, TextBlock, UserMsg

    agent_model = conv.agent

    # ── 1. Build agent (sync, touches DB — offload to thread pool) ──
    agent = await _sta(build_agent)(
        agent_model=agent_model,
        user_id=user_id,
        conversation_id=conv.id,
    )

    # ── 2. Restore conversation context from DB ──
    await _sta(_restore_context)(agent, conv)

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

        if images:
            content_blocks: list = []
            text = user_message.strip()
            if text:
                content_blocks.append(TextBlock(text=text))
            for img in images:
                content_blocks.append(
                    DataBlock(
                        source=Base64Source(
                            data=img["data"],
                            media_type=img["media_type"],
                        )
                    )
                )
            next_input = UserMsg(name=user_id, content=content_blocks)
        else:
            next_input = UserMsg(name=user_id, content=user_message)

        accumulated_text = ""  # accumulated TEXT_BLOCK_DELTA text for backend persistence

        while True:
            async for event in agent.reply_stream(next_input):
                event_dict = event.model_dump()

                # Accumulate text deltas so we can persist the reply even if
                # the browser is closed before the frontend saves it.
                if event_dict.get("type") == "TEXT_BLOCK_DELTA":
                    accumulated_text += event_dict.get("delta", "")

                # If agent requires user confirmation, wait for it via the queue
                if isinstance(event, RequireUserConfirmEvent):
                    json_str = event.model_dump_json()
                    await queue.put(f"data: {json_str}\n\n")

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

                    next_input = UserConfirmResultEvent(  # type: ignore[assignment]
                        reply_id=confirm_data.get("reply_id", ""),
                        confirm_results=confirm_items,  # type: ignore[arg-type]
                    )
                    continue  # Continue the reply loop with confirm result

                # Terminal events — persist AI reply then send the event
                if isinstance(event, (ReplyEndEvent, ExceedMaxItersEvent)):
                    if accumulated_text:
                        try:
                            msg = await _sta(save_message)(
                                conversation_id=conv.id,
                                role="assistant",
                                content=accumulated_text,
                                flow="sse",
                            )
                            event_dict["_backend_msg_id"] = msg.id
                        except Exception:
                            logger.exception(
                                "Failed to persist AI reply for conv=%s",
                                conv.id,
                            )
                    json_str = json.dumps(event_dict, ensure_ascii=False)
                    await queue.put(f"data: {json_str}\n\n")
                    break

                json_str = event.model_dump_json()
                await queue.put(f"data: {json_str}\n\n")

            break  # Exit outer while if inner loop completed naturally

    except asyncio.CancelledError:
        logger.info("Agent task cancelled for conv=%s (newer request arrived)", conv.id)
        await queue.put(None)  # send sentinel so event_generator exits
        raise  # re-raise so the Task properly transitions to cancelled
    except Exception:
        logger.exception("Agent reply_stream failed for conv=%s", conv.id)
        error_event = json.dumps(
            {
                "type": "TEXT_BLOCK_DELTA",
                "block_id": "error",
                "delta": "\n\n[Agent 执行异常，请重试]",
            }
        )
        await queue.put(f"data: {error_event}\n\n")
    finally:
        unregister_agent_session(conv.id)

    # ── Sentinel ──
    await queue.put(None)


def _restore_context(agent, conv: AIConversation) -> None:
    """Restore agent conversation context from saved AIMessage records.

    Loads messages from DB and feeds them into agent.state.context so the
    Agent has full conversation history.

    Called via sync_to_async from the async _agent_stream to avoid
    SynchronousOnlyOperation on the ORM.
    """
    from agentscope.message import AssistantMsg, UserMsg

    messages = list(conv.messages.order_by("created_at"))
    # Current user turn is already saved; exclude it so reply_stream is not duplicated
    if messages and messages[-1].role == "user":
        messages = messages[:-1]

    for msg in messages:
        if msg.role == "user":
            try:
                blocks_data = json.loads(msg.blocks) if msg.blocks else []
            except (json.JSONDecodeError, TypeError):
                blocks_data = []
            if blocks_data and any(
                b.get("type") in ("image", "data") for b in blocks_data if isinstance(b, dict)
            ):
                agent.state.context.append(
                    UserMsg(name="user", content=_dicts_to_blocks(blocks_data)),
                )
            else:
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


_ALLOWED_IMAGE_MEDIA = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _normalize_images(raw_images: list) -> tuple[list[dict], str | None]:
    """Validate and normalize chat/stream images payload. Returns (images, error)."""
    import base64

    if not raw_images:
        return [], None
    if len(raw_images) > 1:
        return [], "每次仅支持上传 1 张图片"

    images: list[dict] = []
    for item in raw_images:
        if not isinstance(item, dict):
            return [], "images 项格式无效"
        media_type = (item.get("media_type") or "").strip().lower()
        data = item.get("data") or ""
        if media_type not in _ALLOWED_IMAGE_MEDIA:
            return [], f"不支持的图片类型: {media_type or '(空)'}"
        if not isinstance(data, str) or not data.strip():
            return [], "图片数据不能为空"
        # Strip data-URI prefix if client sent full URI
        if "," in data and data.strip().startswith("data:"):
            data = data.split(",", 1)[1]
        # Validate base64 before decoding — b64decode(validate=False)
        # silently strips invalid chars instead of rejecting them.
        if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", data):
            return [], "图片 base64 无效"
        try:
            raw = base64.b64decode(data, validate=True)
        except Exception:
            return [], "图片 base64 无效"
        if len(raw) > _MAX_IMAGE_BYTES:
            return [], f"图片过大（最大 {_MAX_IMAGE_BYTES} 字节）"
        images.append({"media_type": media_type, "data": data})
    return images, None


def _build_user_blocks(text: str, images: list[dict]) -> list[dict]:
    """Persistable content blocks for a user message (text + optional image)."""
    blocks: list[dict] = []
    if text:
        blocks.append({"type": "text", "text": text})
    for img in images:
        blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["data"],
                },
            }
        )
    return blocks


def _dicts_to_blocks(blocks_data: list[dict]) -> list:
    """Convert stored block dicts to AgentScope block objects."""
    from agentscope.message import (
        Base64Source,
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
        if not isinstance(b, dict):
            continue
        block_type = b.get("type", "")

        # Stored user image blocks → AgentScope DataBlock
        if block_type == "image":
            source = b.get("source") or {}
            data = source.get("data") or ""
            media_type = source.get("media_type") or "image/png"
            if data:
                try:
                    blocks.append(DataBlock(source=Base64Source(data=data, media_type=media_type)))
                except Exception:
                    pass
            continue

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
                    "done",
                }
                kwargs = {k: v for k, v in b.items() if k in valid_fields and k != "type"}
                if block_type == "data" and isinstance(kwargs.get("source"), dict):
                    src = kwargs["source"]
                    kwargs["source"] = Base64Source(
                        data=src.get("data", ""),
                        media_type=src.get("media_type", "image/png"),
                    )
                blocks.append(cls(**kwargs))
            except Exception:
                # Fallback: wrap as text
                blocks.append(TextBlock(text=str(b.get("text", b.get("output", "")))))  # type: ignore[arg-type]
    return blocks
