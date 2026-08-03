"""Filterable workspace — extends LocalWorkspace with per-agent skill toggles.

AgentScope's LocalWorkspace always exposes all 6 built-in tools
(Bash, Edit, Glob, Grep, Read, Write).  This module provides a
drop-in replacement that respects a per-agent skill-configuration
stored in the Django AIAgent model, so admins can turn individual
workspace tools on / off through the frontend.
"""

from __future__ import annotations

from agentscope.tool import Bash, Edit, Glob, Grep, Read, ToolBase, Write
from agentscope.workspace import LocalWorkspace

# Tool class for each skill name (the name must match ToolBase.name exactly).
_SKILL_CLASS_MAP: dict[str, type[ToolBase]] = {
    "Bash": Bash,
    "Edit": Edit,
    "Glob": Glob,
    "Grep": Grep,
    "Read": Read,
    "Write": Write,
}

# All skill names the frontend can toggle.
ALL_SKILL_NAMES: list[str] = sorted(_SKILL_CLASS_MAP.keys())


class FilterableLocalWorkspace(LocalWorkspace):
    """LocalWorkspace whose ``list_tools()`` can be filtered.

    Pass ``disabled_skills`` to hide a subset of the 6 built-in tools.
    When ``None`` (the default) all six tools are exposed — behaviour
    is identical to the parent class.
    """

    def __init__(self, disabled_skills: set[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._disabled_skills: set[str] = disabled_skills or set()

    async def list_tools(self) -> list[ToolBase]:
        all_tools: list[ToolBase] = await super().list_tools()
        if not self._disabled_skills:
            return all_tools
        return [t for t in all_tools if t.name not in self._disabled_skills]

    def set_disabled_skills(self, disabled: set[str]) -> None:
        """Update the disabled-skill set for the next ``list_tools()`` call."""
        self._disabled_skills = set(disabled)
