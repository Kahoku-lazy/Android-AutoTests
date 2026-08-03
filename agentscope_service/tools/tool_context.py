"""Tool execution context and shared permission helpers."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.permission import PermissionBehavior, PermissionDecision


@dataclass
class ToolContext:
    user_id: str = ""
    agent_id: str = ""
    session_id: str = ""
    jwt: str = ""
    knowledge_sources: list = None


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
