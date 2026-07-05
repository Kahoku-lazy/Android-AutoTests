"""Tool factory — builds the tool list for AgentScope agents from Django config."""
from agentscope.tool import ToolBase, TaskCreate, TaskGet, TaskList, TaskUpdate
from .element_tools import GetTestPointsTool, SearchElementsTool
from .case_tools import SaveTestCaseTool, GetTestCaseTool, ListTestCasesTool, DebugTestCaseTool
from .device_tools import GetOnlineDevicesTool, AcquireDeviceTool, ReleaseDeviceTool
from .runner_tools import RunTestTool, GetRunResultsTool, StopRunTool
from .report_tools import SaveReportTool, ListReportsTool
from .rag_tool import KnowledgeBaseSearchTool
from .task_tools import FetchPageElementsTool, CreateRunnerTaskTool, ListAITasksTool, UpdateAITaskTool, CreateTestSOPTool, UpdateTestSOPTool


# AgentScope built-in Plan tools — for intra-phase sub-task tracking
# These are state-injected (is_state_injected=True), persist in agent.state.tasks_context
_PLAN_TOOLS = [
    TaskCreate(),
    TaskGet(),
    TaskList(),
    TaskUpdate(),
]

# All business tools — platform-specific operations
_ALL_BUSINESS_TOOLS = [
    GetTestPointsTool(),
    SearchElementsTool(),
    FetchPageElementsTool(),
    SaveTestCaseTool(),
    GetTestCaseTool(),
    ListTestCasesTool(),
    DebugTestCaseTool(),
    CreateTestSOPTool(),
    UpdateTestSOPTool(),
    CreateRunnerTaskTool(),
    ListAITasksTool(),
    UpdateAITaskTool(),
    GetOnlineDevicesTool(),
    AcquireDeviceTool(),
    ReleaseDeviceTool(),
    RunTestTool(),
    GetRunResultsTool(),
    StopRunTool(),
    SaveReportTool(),
    ListReportsTool(),
    KnowledgeBaseSearchTool(),
]


async def build_business_tools(user_id: str, agent_id: str, session_id: str) -> list:
    """Factory called by AgentScope's extra_agent_tools before every agent assembly.

    Returns all tools — business tools + AgentScope built-in Plan tools.
    Each tool is self-documenting via its description and input_schema,
    so the LLM naturally selects the right one based on context.

    Two-layer architecture:
    - Plan tools (TaskCreate/List/Update/Get): intra-phase sub-task tracking,
      stored in agent.state.tasks_context, auto-persisted across ReAct rounds.
    - Business tools: platform operations (device/case/element/runner),
      stored in Django DB, cross-session persistent.
    """
    return list(_PLAN_TOOLS) + list(_ALL_BUSINESS_TOOLS)
