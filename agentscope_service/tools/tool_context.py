"""Tool execution context and shared permission helpers."""
from __future__ import annotations

import time
from dataclasses import dataclass

from agentscope.permission import PermissionBehavior, PermissionDecision

STAGED_CASE_TTL_SECONDS = 3600


@dataclass
class ToolContext:
    user_id: str = ""
    agent_id: str = ""
    session_id: str = ""


def check_platform_permission(tool) -> PermissionDecision:
    """Enforce login for write tools; read-only tools always allowed."""
    if getattr(tool, "is_read_only", False):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only.")
    ctx = getattr(tool, "_ctx", None)
    if not ctx or not ctx.user_id:
        return PermissionDecision(
            behavior=PermissionBehavior.DENY,
            message="写操作需要已登录用户。",
        )
    return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Authorized.")


_staged_cases: dict[str, tuple[float, list[dict]]] = {}


def stage_designed_cases(session_id: str, cases: list[dict]) -> None:
    purge_stale_staged_cases()
    _staged_cases[session_id] = (time.time(), list(cases))


def get_staged_cases(session_id: str) -> list[dict]:
    purge_stale_staged_cases()
    entry = _staged_cases.get(session_id)
    return list(entry[1]) if entry else []


def pop_staged_cases(session_id: str) -> list[dict]:
    purge_stale_staged_cases()
    entry = _staged_cases.pop(session_id, None)
    return list(entry[1]) if entry else []


def purge_stale_staged_cases() -> None:
    now = time.time()
    stale = [
        key for key, (ts, _) in _staged_cases.items()
        if now - ts > STAGED_CASE_TTL_SECONDS
    ]
    for key in stale:
        _staged_cases.pop(key, None)
