/** Shared constants for the AI Assistant module. */

// ── Avatar ──

/** 智能体内置头像（public/agent-avatar.svg）。全站唯一，不随智能体数据变化。 */
export const AGENT_AVATAR_SRC = "/agent-avatar.svg"

// ── Platform assistant fixed identity（当前写死，不落库） ──

/** 平台小助手的固定职责 */
export const ASSISTANT_DUTY = "UI自动化"

/** 平台小助手使用的固定工作流 */
export const ASSISTANT_WORKFLOW = "ui_auto_workflow"

// ── 任务类型（AIAgent.task_kind / Task.task_kind） ──

export const TASK_KIND_DEVICE_CONTROL = "device_control"
export const TASK_KIND_CASE_AUTHORING = "case_authoring"

/** Agent-02 的职责 */
export const CASE_AUTHORING_DUTY = "测试用例编写"

/** Agent-02 使用的工作流 */
export const CASE_AUTHORING_WORKFLOW = "case_authoring_workflow"

/** 按任务类型取展示职责。 */
export function agentDuty(taskKind?: string): string {
  return taskKind === TASK_KIND_CASE_AUTHORING ? CASE_AUTHORING_DUTY : ASSISTANT_DUTY
}

/** 按任务类型取展示工作流。 */
export function agentWorkflow(taskKind?: string): string {
  return taskKind === TASK_KIND_CASE_AUTHORING ? CASE_AUTHORING_WORKFLOW : ASSISTANT_WORKFLOW
}

// ── Built-in Tool Names ──

/** Workspace (file-system) tool names — built into the agent runtime. */
export const WORKSPACE_TOOL_NAMES: readonly string[] = [
  "Bash",
  "Edit",
  "Glob",
  "Grep",
  "Read",
  "Write",
]

/** Platform business tool names — registered by the Django backend. */
export const PLATFORM_TOOL_NAMES: readonly string[] = [
  "list_devices",
  "list_apps",
  "acquire_device",
  "release_device",
  "current_app",
  "screenshot_page",
  "list_page_flows",
  "get_page_flow",
]

// ── Timing ──

/** SSE reply watchdog timeout (ms). If no reply within this window, post a disconnect notice.
 *  思考模型 + 多步设备操作（抓屏/点击/导航）单轮可远超 45s，放宽避免误报「等待回复超时」。 */
export const SSE_WATCHDOG_MS = 120_000

/** Delay before resetting model status from "done" → "idle" (ms). */
export const MODEL_STATUS_RESET_MS = 3_000

/** Agent health check interval (ms). */
export const HEALTH_CHECK_INTERVAL_MS = 30 * 60 * 1000

// ── Route Paths ──

export const ROUTE_AI_ASSISTANT = "/ai-assistant"
export const ROUTE_LOGIN = "/login"

/** Build the agent detail/edit route. */
export function agentDetailRoute(id: number | string): string {
  return `/ai-assistant/agent/${id}`
}

// ── Model Status Labels ──

/** Mapping from SSE model status → { label, icon }. */
export const MODEL_STATUS_MAP: Record<string, { label: string; icon: string }> = {
  thinking: { label: "🤔 思考中", icon: "🤔" },
  calling_model: { label: "🧠 调用模型", icon: "🧠" },
  tool_calling: { label: "🔧 调用工具", icon: "🔧" },
  streaming: { label: "✍️ 输出中", icon: "✍️" },
  done: { label: "✅ 已完成", icon: "✅" },
}

// ── Connection Mode Labels ──

export const CONNECTION_MODE_LABELS: Record<string, string> = {
  sse: "SSE 流式通道",
  connecting: "发送时自动连接",
}

export const CONNECTION_MODE_ICONS: Record<string, string> = {
  sse: "⚡",
  connecting: "🔗",
}

// ── Tool Source Labels ──

export const TOOL_SOURCE_LABELS: Record<string, string> = {
  builtin: "内置工具",
  platform: "平台技能",
  mcp: "MCP",
  skill: "Skill",
}

/** Get a human-readable label for a tool source. */
export function toolSourceLabel(source: string | undefined): string {
  return TOOL_SOURCE_LABELS[source ?? ""] ?? "工具"
}
