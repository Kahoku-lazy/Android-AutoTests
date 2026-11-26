from __future__ import annotations

from engines.ae_harness.middleware.control import CancelMiddleware, CancelToken
from engines.ae_harness.middleware.observer import ObservationMiddleware
from engines.backend_bridge.agents.card_agent import build_card_agent

__all__ = [
    "drop_thread",
    "request_thread_cancel",
    "thread_agent",
    "thread_cancel_token",
    "thread_observer",
]

_AGENTS: dict[str, object] = {}
_CANCELS: dict[str, CancelToken] = {}
_OBSERVERS: dict[str, ObservationMiddleware] = {}


async def thread_agent(thread_id: str, snapshot: dict) -> object:
    key = thread_id.strip()
    if not key:
        raise ValueError("thread_id 不能为空")
    current = _AGENTS.get(key)
    if current is not None:
        return current
    observer = ObservationMiddleware(capture_messages=True)
    bundle = await build_card_agent(
        name=str(snapshot.get("name") or "assistant"),
        provider=str(snapshot["provider"]),
        api_key_env=str(snapshot["api_key_env"]),
        model_name=str(snapshot["model_name"]),
        base_url=str(snapshot.get("base_url") or ""),
        system_prompt=str(snapshot.get("system_prompt") or ""),
        tools=list(snapshot.get("tools") or []),
        observers=[CancelMiddleware(thread_cancel_token(key)), observer],
    )
    _AGENTS[key] = bundle.agent
    _OBSERVERS[key] = observer
    return bundle.agent


def thread_observer(thread_id: str) -> ObservationMiddleware | None:
    return _OBSERVERS.get(thread_id.strip())


def thread_cancel_token(thread_id: str) -> CancelToken:
    key = thread_id.strip()
    token = _CANCELS.get(key)
    if token is None:
        token = CancelToken(reason="用户取消")
        _CANCELS[key] = token
    return token


def request_thread_cancel(thread_id: str) -> bool:
    token = _CANCELS.get(thread_id.strip())
    if token is None:
        return False
    token.cancel("用户取消")
    return True


def drop_thread(thread_id: str) -> None:
    key = thread_id.strip()
    _AGENTS.pop(key, None)
    _CANCELS.pop(key, None)
    _OBSERVERS.pop(key, None)
