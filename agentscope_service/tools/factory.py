"""Tool factory — builds the tool list for AgentScope agents from Django config."""

from __future__ import annotations

from agentscope.tool import ToolBase

from apps.ai_assistant.models import AIAgent
from apps.test_runner.models import TestSOP

from .case_tools import (
    CreateDirectoryTool,
    DebugTestCaseTool,
    GetCaseDetailTool,
    GetDirectoryTreeTool,
    GetTestCaseTool,
    ListAllCasesTool,
    ListTestCasesTool,
    SaveApiCaseTool,
    SaveStorageCaseTool,
    SaveTestCaseTool,
    SaveWebCaseTool,
)
from .db_helper import run_sync
from .device_tools import AcquireDeviceTool, GetOnlineDevicesTool, ReleaseDeviceTool
from .element_tools import (
    FetchPageFlowsTool,
    GetTestPointsTool,
    ListPagesTool,
    SearchElementsTool,
)
from .prd_tools import DesignTestCasesFromPRDTool, ImportDesignedCasesTool, ParsePRDTool
from .rag_tool import KnowledgeBaseSearchTool
from .report_tools import ListReportsTool, SaveReportTool
from .runner_tools import GetRunResultsTool, RunTestTool, StopRunTool
from .task_tools import (
    CreateCaseGenTaskTool,
    CreateRunnerTaskTool,
    CreateTestSOPTool,
    FetchPageElementsTool,
    ListAITasksTool,
    ListWorkflowDocumentsTool,
    UpdateAITaskTool,
    UpdateCaseGenTaskTool,
    UpdateTestSOPTool,
)
from .tool_context import ToolContext

_TOOL_REGISTRY: list[type[ToolBase]] = [
    GetTestPointsTool,
    SearchElementsTool,
    ListPagesTool,
    FetchPageFlowsTool,
    FetchPageElementsTool,
    GetDirectoryTreeTool,
    CreateDirectoryTool,
    ListAllCasesTool,
    GetCaseDetailTool,
    SaveTestCaseTool,
    SaveStorageCaseTool,
    SaveApiCaseTool,
    SaveWebCaseTool,
    GetTestCaseTool,
    ListTestCasesTool,
    DebugTestCaseTool,
    CreateTestSOPTool,
    UpdateTestSOPTool,
    CreateRunnerTaskTool,
    CreateCaseGenTaskTool,
    UpdateCaseGenTaskTool,
    ListWorkflowDocumentsTool,
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
    ListPagesTool.name,
    FetchPageFlowsTool.name,
    FetchPageElementsTool.name,
    GetDirectoryTreeTool.name,
    ListAllCasesTool.name,
    GetCaseDetailTool.name,
    GetTestCaseTool.name,
    ListTestCasesTool.name,
    ListWorkflowDocumentsTool.name,
    ListAITasksTool.name,
    GetOnlineDevicesTool.name,
    GetRunResultsTool.name,
    ListReportsTool.name,
    KnowledgeBaseSearchTool.name,
    ParsePRDTool.name,
}


def _resolve_enabled_names(agent_id: str) -> set[str]:
    """Return enabled platform tool names for an agent.

    - Agent not found / DB error → all registry tools (safety fallback).
    - No matching AITool rows → empty set (no tools loaded).
    - Matching rows but all disabled → read-only subset.
    - Otherwise → enabled matching names only.
    """
    try:
        agent = AIAgent.objects.prefetch_related("tools").get(id=int(agent_id))
    except (AIAgent.DoesNotExist, ValueError, TypeError):
        return set(_REGISTRY_NAMES)

    platform_tools = [t for t in agent.tools.all() if t.name in _REGISTRY_NAMES]
    if not platform_tools:
        return set()  # No configuration → no platform tools loaded

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


def _get_current_sop_phase(session_id: str) -> int | None:
    """Resolve the current SOP phase for a given AgentScope session.

    Looks up AIConversation by agent_scope_session_id, then TestSOP by conv_id.
    Returns the phase number (1-4) or None if no SOP exists yet.
    """
    from apps.ai_assistant.models import AIConversation

    try:
        conv = AIConversation.objects.filter(agent_scope_session_id=session_id).first()
        if conv is None:
            return None
        sop = TestSOP.objects.filter(conv_id=conv.id).order_by("-updated_at").first()
        if sop is None:
            return None
        return sop.phase
    except Exception:
        return None


def _apply_phase_filter(enabled_names: set[str], agent_id: str, session_id: str) -> set[str]:
    """Filter tool names by the agent's phase_tool_config for the current SOP phase.

    Returns the filtered set (may be unchanged if no config or no phase found).
    """
    try:
        agent = AIAgent.objects.get(id=int(agent_id))
    except (AIAgent.DoesNotExist, ValueError, TypeError):
        return enabled_names

    config = agent.phase_tool_config or {}
    if not config:
        return enabled_names  # No phase config → all tools allowed

    phase = _get_current_sop_phase(session_id)
    if phase is None:
        return enabled_names  # No SOP yet → don't filter

    phase_key = str(phase)
    phase_tool_names = config.get(phase_key)
    if not phase_tool_names:
        return enabled_names  # Phase not configured → all tools allowed

    # Intersection: only keep tools that are both enabled AND in the phase list
    phase_set = set(phase_tool_names)
    return enabled_names & phase_set


async def build_business_tools(user_id: str, agent_id: str, session_id: str) -> list:
    """Build agent-filtered business tools with per-call context.

    Applies two layers of filtering:
      1. ai_tools table — per-agent enable/disable (via _resolve_enabled_names).
      2. phase_tool_config — per-SOP-phase tool subsets (optional, configurable in UI).

    Plan tools (TaskCreate/Get/List/Update) are provided natively by
    the AgentScope framework — we only supply platform business tools here.
    """
    ctx = ToolContext(
        user_id=str(user_id or ""),
        agent_id=str(agent_id or ""),
        session_id=str(session_id or ""),
    )
    enabled_names = await run_sync(lambda: _resolve_enabled_names(agent_id))
    # Apply SOP phase filter if configured
    if enabled_names:
        enabled_names = await run_sync(
            lambda: _apply_phase_filter(enabled_names, agent_id, session_id)
        )
    return _instantiate_tools(enabled_names, ctx)
