from __future__ import annotations

import asyncio
import atexit
import threading

from typing import Any, Coroutine, TypeVar

__all__ = ["run_in_loop", "stop_loop"]

T = TypeVar("T")

_guard = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None


def _serve(holder: list[asyncio.AbstractEventLoop], ready: threading.Event) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    holder.append(loop)
    ready.set()
    loop.run_forever()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _loop
    with _guard:
        if _loop is not None and _loop.is_running():
            return _loop
        holder: list[asyncio.AbstractEventLoop] = []
        ready = threading.Event()
        threading.Thread(
            target=_serve,
            args=(holder, ready),
            name="ai-assistant-agent-loop",
            daemon=True,
        ).start()
        if not ready.wait(timeout=10):
            raise RuntimeError("执行循环启动超时")
        _loop = holder[0]
        return _loop


def run_in_loop(coro: Coroutine[Any, Any, T]) -> T:
    loop = _ensure_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def stop_loop() -> None:
    loop = _loop
    if loop is None:
        return
    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        return


atexit.register(stop_loop)
