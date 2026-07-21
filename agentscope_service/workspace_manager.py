"""Custom workspace manager — creates FilterableLocalWorkspace instances.

Extends AgentScope's LocalWorkspaceManager so that per-agent skill
configuration (stored in the Django ``AIAgent.skills_config`` field)
is applied to every workspace before tools are listed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time

from agentscope.app.workspace_manager._local_workspace_manager import (
    LocalWorkspaceManager,
)
from agentscope.workspace import LocalWorkspace

from .filterable_workspace import FilterableLocalWorkspace

logger = logging.getLogger("agentscope")


class FilterableLocalWorkspaceManager(LocalWorkspaceManager):
    """LocalWorkspaceManager that injects skill filters from Django DB.

    On every ``get_workspace()`` call, reads the agent's ``skills_config``
    from the database and calls ``set_disabled_skills()`` on the cached
    workspace so the next ``list_tools()`` reflects the current config.
    """

    async def get_workspace(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
        workspace_id: str,
    ) -> LocalWorkspace:
        ws = await super().get_workspace(
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            workspace_id=workspace_id,
        )
        # Ensure it's our filterable type and apply current config
        if isinstance(ws, FilterableLocalWorkspace):
            disabled = await self._load_disabled_skills(agent_id)
            ws.set_disabled_skills(disabled)
        return ws

    async def create_workspace(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
    ) -> LocalWorkspace:
        ws = await super().create_workspace(
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
        )
        if isinstance(ws, FilterableLocalWorkspace):
            disabled = await self._load_disabled_skills(agent_id)
            ws.set_disabled_skills(disabled)
        return ws

    # ── override the factory so the concrete class is FilterableLocalWorkspace ──

    async def _build_workspace(self, workdir: str) -> FilterableLocalWorkspace:
        """Create a FilterableLocalWorkspace instead of LocalWorkspace."""
        ws = FilterableLocalWorkspace(
            workdir=workdir,
            default_mcps=self._default_mcps,
            skill_paths=self._skill_paths,
        )
        await ws.initialize()
        return ws

    # ── DB helpers ──

    @staticmethod
    async def _load_disabled_skills(agent_id: str) -> set[str]:
        """Read the agent's skills_config from Django and return disabled
        skill names.

        ``skills_config`` is expected to be a JSON object like::

            {"Bash": true, "Read": true, "Write": false, ...}

        Any skill whose value is ``false`` (or missing from the config
        entirely) is considered *disabled*.
        """
        try:
            from apps.ai_assistant.models import AIAgent

            agent = await asyncio.to_thread(
                lambda: AIAgent.objects.filter(
                    agent_scope_id=agent_id,
                ).first(),
            )
            if agent is None:
                # Try by Django PK as fallback
                agent = await asyncio.to_thread(
                    lambda: AIAgent.objects.filter(id=int(agent_id)).first()
                    if agent_id.isdigit()
                    else None,
                )
        except Exception:
            logger.debug(
                "Cannot load skills_config for agent %s", agent_id, exc_info=True,
            )
            return set()

        if agent is None:
            return set()

        cfg = agent.skills_config or {}
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except (json.JSONDecodeError, TypeError):
                cfg = {}

        from .filterable_workspace import ALL_SKILL_NAMES

        disabled = set()
        for name in ALL_SKILL_NAMES:
            if not cfg.get(name, True):  # default: enabled
                disabled.add(name)

        return disabled

    # ── Override _get_or_create to use our workspace class ──

    async def _get_or_build(self, workspace_id, agent_id, workdir):
        """Build a FilterableLocalWorkspace when cache misses."""
        ws = FilterableLocalWorkspace(
            workspace_id=workspace_id,
            workdir=workdir,
            default_mcps=self._default_mcps,
            skill_paths=self._skill_paths,
        )
        await ws.initialize()
        return ws


# ── Monkey-patch to make LocalWorkspaceManager use FilterableLocalWorkspace ──
# We override the internal factory method so both get_workspace (cache miss)
# and create_workspace produce FilterableLocalWorkspace instances.

_original_get_workspace = LocalWorkspaceManager.get_workspace


async def _patched_get_workspace(
    self: LocalWorkspaceManager,
    user_id: str,
    agent_id: str,
    session_id: str,
    workspace_id: str,
) -> LocalWorkspace:
    # Call the original to get the workspace (possibly cached)
    ws = await _original_get_workspace(
        self, user_id, agent_id, session_id, workspace_id,
    )
    # Patch the workspace to be filterable if it isn't already
    if type(ws) is LocalWorkspace:  # exact match, not subclass
        _patch_workspace_to_filterable(ws)
    # Apply current skill config
    disabled = await FilterableLocalWorkspaceManager._load_disabled_skills(
        agent_id,
    )
    if hasattr(ws, "set_disabled_skills"):
        ws.set_disabled_skills(disabled)
    return ws


def _patch_workspace_to_filterable(ws: LocalWorkspace) -> None:
    """Dynamically make a LocalWorkspace support skill filtering."""
    if hasattr(ws, "_disabled_skills"):
        return  # already patched

    ws._disabled_skills = set()
    _original_list_tools = ws.list_tools

    async def _filtered_list_tools() -> list:
        tools = await _original_list_tools()
        disabled = getattr(ws, "_disabled_skills", set())
        if not disabled:
            return tools
        return [t for t in tools if t.name not in disabled]

    ws.list_tools = _filtered_list_tools
    ws.set_disabled_skills = lambda d: setattr(ws, "_disabled_skills", set(d))


def install_filterable_workspace_manager():
    """Monkey-patch LocalWorkspaceManager to use filterable workspaces.

    Call once at AgentScope startup, before any workspaces are created.
    This avoids having to subclass AgentScope's internal factory classes.
    """
    LocalWorkspaceManager.get_workspace = _patched_get_workspace
    logger.info("Filterable workspace manager installed")
