"""Tool factory — builds the tool list for AgentScope agents from Django config."""
from __future__ import annotations

from agentscope.tool import TaskCreate, TaskGet, TaskList, TaskUpdate, ToolBase

from apps.ai_assistant.models import AIAgent

from .case_tools import (
    DebugTestCaseTool,
    GetTestCaseTool,
    ListTestCasesTool,
    SaveTestCaseTool,
)
from .db_helper import run_sync
from .device_tools import AcquireDeviceTool, GetOnlineDevicesTool, ReleaseDeviceTool
from .element_tools import GetTestPointsTool, SearchElementsTool
from .prd_tools import DesignTestCasesFromPRDTool, ImportDesignedCasesTool, ParsePRDTool
from .rag_tool import KnowledgeBaseSearchTool
from .report_tools import ListReportsTool, SaveReportTool
from .runner_tools import GetRunResultsTool, RunTestTool, StopRunTool
from .task_tools import (
    CreateRunnerTaskTool,
    CreateTestSOPTool,
    FetchPageElementsTool,
    ListAITasksTool,
    UpdateAITaskTool,
    UpdateTestSOPTool,
)
from .tool_context import ToolContext

_TOOL_REGISTRY: list[type[ToolBase]] = [
    GetTestPointsTool,
    SearchElementsTool,
    FetchPageElementsTool,
    SaveTestCaseTool,
    GetTestCaseTool,
    ListTestCasesTool,
    DebugTestCaseTool,
    CreateTestSOPTool,
    UpdateTestSOPTool,
    CreateRunnerTaskTool,
    ListAITasksTool,
    UpdateAITaskTool,
    GetOnlineDevicesTool,
    AcquireDeviceTool,
    ReleaseDeviceTool,
    RunTestTool,
    GetRunResultsTool,
    StopRunTool,
    SaveReportTool,
    ListReportsTool,
    KnowledgeBaseSearchTool,
    ParsePRDTool,
    DesignTestCasesFromPRDTool,
    ImportDesignedCasesTool,
]

_REGISTRY_NAMES = {cls.name for cls in _TOOL_REGISTRY}

# Read-only subset used when agent explicitly disables all platform tools.
_READ_ONLY_TOOL_NAMES = {
    GetTestPointsTool.name,
    SearchElementsTool.name,
    FetchPageElementsTool.name,
    GetTestCaseTool.name,
    ListTestCasesTool.name,
    ListAITasksTool.name,
    GetOnlineDevicesTool.name,
    GetRunResultsTool.name,
    ListReportsTool.name,
    KnowledgeBaseSearchTool.name,
    ParsePRDTool.name,
}


def _build_plan_tools() -> list:
    return [TaskCreate(), TaskGet(), TaskList(), TaskUpdate()]


def _resolve_enabled_names(agent_id: str) -> set[str]:
    """Return enabled platform tool names for an agent.

    - No matching AITool rows → all registry tools (legacy default).
    - Matching rows but all disabled → read-only subset.
    - Otherwise → enabled matching names only.
    """
    try:
        agent = AIAgent.objects.prefetch_related("tools").get(id=int(agent_id))
    except (AIAgent.DoesNotExist, ValueError, TypeError):
        return set(_REGISTRY_NAMES)

    platform_tools = [t for t in agent.tools.all() if t.name in _REGISTRY_NAMES]
    if not platform_tools:
        return set(_REGISTRY_NAMES)

    enabled = {t.name for t in platform_tools if t.enabled}
    if enabled:
        return enabled
    return set(_READ_ONLY_TOOL_NAMES)


def _instantiate_tools(enabled_names: set[str], ctx: ToolContext) -> list:
    tools = []
    for cls in _TOOL_REGISTRY:
        if cls.name not in enabled_names:
            continue
        tool = cls()
        tool._ctx = ctx
        tools.append(tool)
    return tools


async def build_business_tools(user_id: str, agent_id: str, session_id: str) -> list:
    """Build Plan tools + agent-filtered business tools with per-call context."""
    ctx = ToolContext(
        user_id=str(user_id or ""),
        agent_id=str(agent_id or ""),
        session_id=str(session_id or ""),
    )
    enabled_names = await run_sync(lambda: _resolve_enabled_names(agent_id))
    return _build_plan_tools() + _instantiate_tools(enabled_names, ctx)
