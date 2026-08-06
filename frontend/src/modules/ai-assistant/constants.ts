/** Shared constants for the AI Assistant module. */

// ── Avatar / Image ──

export const AVATAR_PATH_PREFIX = "/api/ai/avatars/"
export const DATA_IMAGE_PREFIX = "data:image/"

/** Check whether an avatar string is an image URL (uploaded avatar or data URI). */
export function isImageAvatar(av: string | null | undefined): boolean {
  if (!av) return false
  return av.startsWith(AVATAR_PATH_PREFIX) || av.startsWith(DATA_IMAGE_PREFIX)
}

// ── Built-in Tool Names ──

/** Workspace (file-system) tool names — built into the agent runtime. */
export const WORKSPACE_TOOL_NAMES: readonly string[] = [
  "Bash", "Edit", "Glob", "Grep", "Read", "Write",
]

/** Platform business tool names — registered by the Django backend. */
export const PLATFORM_TOOL_NAMES: readonly string[] = [
  "get_online_devices", "acquire_device", "release_device",
  "search_elements", "get_test_points", "list_pages", "fetch_page_elements",
  "save_test_case", "list_test_cases", "get_test_case", "delete_test_case",
  "run_test", "get_run_results", "get_run_status",
  "search_knowledge_base",
]

// ── Timing ──

/** SSE reply watchdog timeout (ms). If no reply within this window, post a disconnect notice. */
export const SSE_WATCHDOG_MS = 45_000

/** Delay before resetting model status from "done" → "idle" (ms). */
export const MODEL_STATUS_RESET_MS = 3_000

/** Evaluator run polling interval (ms). */
export const EVALUATOR_POLL_MS = 2_000

/** Default top-k for knowledge base search. */
export const KB_SEARCH_TOP_K = 5

/** Agent health check interval (ms). */
export const HEALTH_CHECK_INTERVAL_MS = 30 * 60 * 1000

/** Task refresh interval when tasks are running (ms). */
export const TASK_REFRESH_INTERVAL_MS = 15_000

// ── Route Paths ──

export const ROUTE_AI_ASSISTANT = "/ai-assistant"
export const ROUTE_AGENT_DETAIL = "/ai-assistant/agent/:agentId"
export const ROUTE_AGENT_CHAT = "/ai-assistant/chat/:agentId"
export const ROUTE_LOGIN = "/login"
export const ROUTE_CASES = "/cases"
export const ROUTE_RUNNER = "/runner"

/** Build the chat route for a specific agent. */
export function chatRoute(agentId: number | string): string {
  return `/ai-assistant/chat/${agentId}`
}

/** Build the agent detail/edit route. */
export function agentDetailRoute(id: number | string): string {
  return `/ai-assistant/agent/${id}`
}

/** Build the runner route for a run ID. */
export function runnerRoute(runId: string): string {
  return `/runner?run=${encodeURIComponent(runId)}`
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
