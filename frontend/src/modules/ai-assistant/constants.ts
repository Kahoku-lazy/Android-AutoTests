/** Shared constants for the AI Assistant module. */

// ── Avatar / Image ──

export const DATA_IMAGE_PREFIX = "data:image/"

/** Check whether an avatar string is an image URL (data URI). */
export function isImageAvatar(av: string | null | undefined): boolean {
  if (!av) return false
  return av.startsWith(DATA_IMAGE_PREFIX)
}

// ── Built-in Tool Names ──

/** Workspace (file-system) tool names — built into the agent runtime. */
export const WORKSPACE_TOOL_NAMES: readonly string[] = [
  "Bash", "Edit", "Glob", "Grep", "Read", "Write",
]

/** Platform business tool names — registered by the Django backend. */
export const PLATFORM_TOOL_NAMES: readonly string[] = [
  "get_online_devices", "acquire_device", "release_device",
  "search_elements", "list_pages", "fetch_page_elements",
  "save_case", "get_case", "save_api_test_case", "debug_case",
  "run_test", "get_run_results", "stop_run",
  "search_knowledge_base",
]

// ── Timing ──

/** SSE reply watchdog timeout (ms). If no reply within this window, post a disconnect notice.
 *  思考模型 + 多步设备操作（抓屏/点击/导航）单轮可远超 45s，放宽避免误报「等待回复超时」。 */
export const SSE_WATCHDOG_MS = 120_000

/** Delay before resetting model status from "done" → "idle" (ms). */
export const MODEL_STATUS_RESET_MS = 3_000

/** Evaluator run polling interval (ms). */
export const EVALUATOR_POLL_MS = 2_000

/** Default top-k for knowledge base search. */
export const KB_SEARCH_TOP_K = 5

/** Agent health check interval (ms). */
export const HEALTH_CHECK_INTERVAL_MS = 30 * 60 * 1000

// ── Route Paths ──

export const ROUTE_AI_ASSISTANT = "/ai-assistant"
export const ROUTE_LOGIN = "/login"

/** Build the agent detail/edit route. */
export function agentDetailRoute(id: number | string): string {
  return `/ai-assistant/agent/${id}`
}

/** 智能体线路（任务卡片「智能体」下拉） */
export const AGENT_ROUTES = [
  { value: 'device_control', label: '控制设备' },
  { value: 'platform_task', label: '平台任务' },
] as const

export const ROUTE_LABELS: Record<string, string> = {
  device_control: '控制设备',
  platform_task: '平台任务',
}

export const ROUTE_ICONS: Record<string, string> = {
  device_control: '📱',
  platform_task: '🧭',
}

/** 任务卡片列表筛选（顺序：全部 → 平台任务 → 控制设备） */
export const TASK_FILTER_TABS = {
  all: { label: '全部任务' },
  platform_task: { label: '平台任务' },
  device_control: { label: '控制设备' },
} as const

/** 任务卡片六态（PRD-08-01：待执行 / 执行中 / 任务成功 / 任务失败 / 任务取消 / 任务暂停） */
export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '执行中',
  completed: '任务成功',
  success: '任务成功',
  failed: '任务失败',
  cancelled: '任务取消',
  paused: '任务暂停',
}

export type TaskStatusTone = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'paused'

export function taskStatusTone(status: string): TaskStatusTone {
  const key = (status || '').toLowerCase()
  if (key === 'running') return 'running'
  if (key === 'completed' || key === 'success') return 'success'
  if (key === 'failed') return 'failed'
  if (key === 'paused') return 'paused'
  if (key === 'cancelled') return 'cancelled'
  return 'pending'
}

export function taskStatusLabel(status: string): string {
  return TASK_STATUS_LABELS[(status || '').toLowerCase()] || status || '待执行'
}

// ── Model Status Labels ──

/** Mapping from SSE model status → { label, icon }. */
export const MODEL_STATUS_MAP: Record<string, { label: string; icon: string }> = {
  thinking:       { label: "🤔 思考中",   icon: "🤔" },
  calling_model:  { label: "🧠 调用模型", icon: "🧠" },
  tool_calling:   { label: "🔧 调用工具", icon: "🔧" },
  streaming:      { label: "✍️ 输出中",   icon: "✍️" },
  done:           { label: "✅ 已完成",   icon: "✅" },
}

// ── Connection Mode Labels ──

export const CONNECTION_MODE_LABELS: Record<string, string> = {
  sse:         "SSE 流式通道",
  connecting:  "发送时自动连接",
}

export const CONNECTION_MODE_ICONS: Record<string, string> = {
  sse:         "⚡",
  connecting:  "🔗",
}

// ── Tool Source Labels ──

export const TOOL_SOURCE_LABELS: Record<string, string> = {
  builtin:  "内置工具",
  platform: "平台技能",
  mcp:      "MCP",
  skill:    "Skill",
}

/** Get a human-readable label for a tool source. */
export function toolSourceLabel(source: string | undefined): string {
  return TOOL_SOURCE_LABELS[source ?? ""] ?? "工具"
}
