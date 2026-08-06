"""Workspace skill registry — maps tool class names to AgentScope built-in tools.

Previously lives in agentscope_service/filterable_workspace.py.
Moved here so agentscope_service/ can be removed entirely.
"""

from agentscope.tool import Bash, Edit, Glob, Grep, Read, ToolBase, Write

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
