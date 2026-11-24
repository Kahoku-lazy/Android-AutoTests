from __future__ import annotations

from engines.ae_harness.middleware.control import CancelMiddleware, CancelToken

__all__ = [
    "bind_cancel",
    "cancel_controls",
    "clear_cancel",
    "request_cancel",
]

_TOKENS: dict[int, CancelToken] = {}


def bind_cancel(task_id: int, *, reason: str = "用户取消") -> CancelToken:
    if not task_id:
        return CancelToken(reason=reason)
    key = int(task_id)
    existing = _TOKENS.get(key)
    if existing is not None:
        return existing
    token = CancelToken(reason=reason)
    _TOKENS[key] = token
    return token


def request_cancel(task_id: int, reason: str = "用户取消") -> bool:
    token = _TOKENS.get(int(task_id or 0))
    if token is None:
        return False
    token.cancel(reason)
    return True


def clear_cancel(task_id: int) -> None:
    _TOKENS.pop(int(task_id or 0), None)


def cancel_controls(task_id: int) -> list:
    token = _TOKENS.get(int(task_id or 0))
    return [CancelMiddleware(token)] if token is not None else []
