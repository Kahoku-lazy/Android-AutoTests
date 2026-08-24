"""HITL 会话注册表与确认投递 — 与 SSE 事件循环（chat_views）耦合的内存实现。

Batch 2：确认端点已迁至 DRF（views_drf.ConversationViewSet.confirm_result），
本文件保留注册表 + 投递函数（chat_stream 与 DRF 视图共用）。
"""

import asyncio
import logging
import threading

logger = logging.getLogger("ai_assistant")

# ── In-memory agent session registry ──
# Maps conv_id → asyncio.Queue used to deliver HITL confirm results to the
# running Agent's event loop. The chat_stream view registers the queue when
# streaming starts; deliver_confirm_result puts results into it.
_agent_sessions: dict[int, dict] = {}
_sessions_lock = threading.Lock()

# Reference to the main event loop (Daphne's loop) for thread-safe queue delivery.
# Set by chat_stream on first use. deliver_confirm_result (sync, runs in
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


def deliver_confirm_result(
    conv_id: int, reply_id: str, confirm_results: list
) -> tuple[int, str] | None:
    """向运行中的 Agent 会话投递 HITL 确认结果。

    成功返回 None；失败返回 (status_code, message)：
      (400, ...) 无活跃会话；(409, ...) 队列已满。
    """
    with _sessions_lock:
        session = _agent_sessions.get(conv_id)
        if session is None:
            return 400, "No active agent session — the conversation may have ended or timed out"

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
            return 409, "Agent is busy — please try again"

    return None
