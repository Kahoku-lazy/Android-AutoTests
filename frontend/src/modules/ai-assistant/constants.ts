/** Shared constants for the AI Assistant module. */

import type { ModelDebugLogBasis } from "@/shared/types/ai"

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
  "app_control",
  "tap_screen",
  "swipe_screen",
  "press_key",
  "input_text",
  "current_app",
  "click_ratio",
  "drag_ratio",
  "xpath_action",
  "screenshot_page",
  "list_page_flows",
  "get_page_flow",
]

// ── Timing ──

/** 新建任务设备下拉轮询间隔，与设备管理 HEARTBEAT_INTERVAL（30s）对齐 */
export const TASK_DEVICE_POLL_INTERVAL_MS = 30000

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

/** 任务详情全屏页 */
export function taskDetailRoute(id: number | string): string {
  return `/ai-assistant/tasks/${id}`
}

/** Skill 内容查看页 */
export function skillViewerRoute(name: string): string {
  return `/ai-assistant/toolbox/skills/${encodeURIComponent(name)}`
}

/** 平台工具调试页 */
export function toolDebugRoute(name: string): string {
  return `/ai-assistant/toolbox/tools/${encodeURIComponent(name)}`
}

/** 调试台角色分段项（页内完整角色名取自接口 role.label） */
export const MODEL_DEBUG_ROLE_TABS = [
  { role: "planner", label: "规划模型" },
  { role: "executor", label: "执行模型" },
  { role: "verifier", label: "验收模型" },
] as const

/** 单模型调试页（role = planner / executor / verifier） */
export function modelDebugRoute(role: string): string {
  return `/ai-assistant/toolbox/models/${encodeURIComponent(role)}`
}

// ── 模型调试：三层语义分区标题（编号与规格口径一致：角色带① / 生效装配② / 参考数据③）──

export const MODEL_DEBUG_LAYER_TITLES = {
  role: "① 角色带 · 当前是谁",
  assembly: "② 生效装配 · 能干什么",
  reference: "③ 参考数据 · 有哪些资产",
  chat: "调试对话 · 常驻右栏",
} as const

// ── 模型调试：生效装配区底部如实描述当前行为（挂真实工具、会真机操作）──

/** 调试对话实际挂载该角色工具子集，故不得再写「不挂工具 / 不碰真机」 */
export const MODEL_DEBUG_ASSEMBLY_NOTE =
  "调试对话挂载上述工具：会真实调用该角色工具子集，需要设备的角色会真实操作所选设备；对话不落库"

// ── 模型调试：参考数据区（设备与 Skill 目录，整区只读）──

/** 参考数据区设备块的资格徽标（该角色是否需要设备） */
export const MODEL_DEBUG_DEVICE_NEEDED_BADGE = "需要设备"

export const MODEL_DEBUG_DEVICE_NOT_NEEDED_BADGE = "不需要设备"

/** 该角色工具子集不含设备操作工具时的如实说明 */
export const MODEL_DEBUG_DEVICE_NOT_NEEDED_NOTE =
  "该角色工具子集不含设备操作工具，调试对话不会操作设备"

export const MODEL_DEBUG_DEVICE_EMPTY_NOTE = "当前没有可用设备（需对当前用户可见、在线且未被占用）"

export const MODEL_DEBUG_DEVICE_LOADING_NOTE = "正在加载可用设备…"

/** 参考数据区 Skill 目录块标题（列目录路径，与生效装配区的清单区分） */
export const MODEL_DEBUG_SKILL_DIR_TITLE = "Skill 目录"

export const MODEL_DEBUG_SKILL_DIR_EMPTY_NOTE = "总闸已开，但目录下没有可用 Skill"

export const MODEL_DEBUG_SKILL_GATE_OFF_NOTE = "「自定义 Skill」总闸未开"

// ── 模型调试：归属标注（避免让人误以为按角色分配）──

/** Skill 是三模型共用（装配链路整组传同一批目录，非按角色分配） */
export const SKILL_SHARED_NOTE = "三模型共用（装配时整组下发，非按角色分配）"

// ── 模型调试：调试对话的区块标题（返回结果与思考过程必须一眼可分）──

/** 助手消息里「模型返回结果」区块的标题 */
export const MODEL_DEBUG_ANSWER_LABEL = "回复"

/** 助手消息里调用失败时该区块的标题 */
export const MODEL_DEBUG_ANSWER_ERROR_LABEL = "调用失败"

/** 助手消息里「模型思考过程」区块的标题 */
export const MODEL_DEBUG_THINKING_LABEL = "思考过程"

/** 助手消息里「工具调用」轨迹区块的标题 */
export const MODEL_DEBUG_TRACE_LABEL = "工具调用"

/** 轨迹里单条入参/返回的最大展示字符数（action_time / screenshot_path 这类尾部字段必须看得到，故留足余量） */
export const MODEL_DEBUG_TRACE_DETAIL_MAX = 600

/** 调试范围说明：如实描述当前行为（挂真实工具、会真机操作） */
export const MODEL_DEBUG_SCOPE_NOTE =
  "只发这一个角色 · 挂载该角色真实工具 · 会真实操作所选设备 · 对话不落库"

/** 需要设备的角色未选设备时的提示 */
export const MODEL_DEBUG_DEVICE_REQUIRED_HINT = "请先选择调试设备（需可见 + 在线 + 未被占用）"

/** 真机调试发送前的二次确认标题 */
export const MODEL_DEBUG_DEVICE_CONFIRM_TITLE = "确认真机调试？"

/** 真机调试二次确认正文：必须写明目标设备与写工具数量 */
export function modelDebugDeviceConfirmText(deviceLabel: string, writeToolCount: number): string {
  const scope =
    writeToolCount > 0
      ? `将挂载 ${writeToolCount} 个写工具，会真实操作该设备`
      : "本次只挂只读工具，不会修改该设备"
  return `目标设备：${deviceLabel}\n${scope}。是否继续？`
}

/** 任务详情：执行侧「日志检查」区块（StepLogCheck）文案 */
export const STEP_LOG_CHECK_TITLE = "日志检查"

/** 本步带有需日志核对的断言时的说明（区块头部） */
export const STEP_LOG_CHECK_HINT = "本步断言需核对设备日志 · 取证窗 5 秒"

/** 某次点击之后确实没截图时如实标注 */
export const STEP_LOG_CHECK_NO_SHOT_TEXT = "该次点击后未截图"

/** 任务详情：执行结果段里本步没有截图时如实标注（新执行契约的 screenshot 为空串） */
export const STEP_EXEC_NO_SHOT_TEXT = "该步未截图"

/** 模型调试：验收对话的日志证据区块（调试回溯，不改变生产的 5 秒取证窗口径） */
export const MODEL_DEBUG_LOG_BASIS_LABEL = "日志证据 · 调试回溯"

/** 本轮检查的日志关键词（平台按检查工具调用自动填） */
export const MODEL_DEBUG_LOG_ASSERTION_LABEL = "本轮检查的日志关键词"

export const MODEL_DEBUG_LOG_BASIS_NOTE =
  "平台按取证基准从日志文件回溯取出，判定口径与任务链路一致；这是调试回溯，不是生产步骤的取证窗"

/** 调试日志证据的基准说明（基准时刻 + 来源 + 读取的文件 + 取不到时的原因） */
export function modelDebugLogBasisText(basis: ModelDebugLogBasis): string {
  const origin = basis.from_message ? "消息里的时刻" : "最近一个取证窗"
  const files = basis.files?.length ? ` · 读取 ${basis.files.length} 个日志文件` : ""
  const note = basis.note ? ` · ${basis.note}` : ""
  return `取证基准 ${basis.basis_time || "—"}（来源：${origin}）${files}${note} · ${MODEL_DEBUG_LOG_BASIS_NOTE}`
}

/** 工具箱「日志关键词」来源（只读表格）文案 */
export const LOG_KEYWORD_SEARCH_PLACEHOLDER = "搜索关键词 / 功能模块 / 功能点…"

/** 表格三列（一行一个「关键词 × 功能点」） */
export const LOG_KEYWORD_COL_KEYWORD = "关键词"
export const LOG_KEYWORD_COL_MODULE = "功能模块"
export const LOG_KEYWORD_COL_FEATURE = "功能点"

/** 取值来源的中文口径（后端 origin 字段） */
export const LOG_KEYWORD_ORIGIN_LABELS: Record<string, string> = {
  runtime: "运行中的采集索引",
  file: "关键词表文件",
  none: "未取到",
}

/** 改表生效时机：判定用的是平台启动时加载的那份表 */
export const LOG_KEYWORD_RESTART_HINT = "改关键词表后需重启平台才用于判定"

export const LOG_KEYWORD_EMPTY_TEXT = "暂无可用的日志关键词"

export const LOG_KEYWORD_EMPTY_HINT =
  "关键词表文件缺失或尚未生成：检查 DEVICE_LOG_KEYWORD_FILE 指向的文件"

export const LOG_KEYWORD_NO_MATCH_TEXT = "没有匹配的关键词"

/** 智能体线路（任务卡片「智能体」下拉） */
export const AGENT_ROUTES = [{ value: "device_control", label: "控制设备" }] as const

export const ROUTE_LABELS: Record<string, string> = {
  device_control: "控制设备",
}

export const ROUTE_ICONS: Record<string, string> = {
  device_control: "📱",
}

/** 任务卡片列表筛选（仅全部） */
export const TASK_FILTER_TABS = {
  all: { label: "全部任务" },
} as const

/** 任务卡片六态（待执行 / 执行中 / 任务成功 / 任务失败 / 任务取消 / 任务暂停） */
export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: "待执行",
  running: "执行中",
  completed: "任务成功",
  success: "任务成功",
  failed: "任务失败",
  cancelled: "任务取消",
  paused: "任务暂停",
}

export type TaskStatusTone = "pending" | "running" | "success" | "failed" | "cancelled" | "paused"

/** 任务看板按状态分组的展示顺序（completed/success 合并为「任务成功」） */
export const TASK_STATUS_GROUPS: { key: TaskStatusTone; label: string }[] = [
  { key: "pending", label: "待执行" },
  { key: "running", label: "执行中" },
  { key: "paused", label: "任务暂停" },
  { key: "success", label: "任务成功" },
  { key: "failed", label: "任务失败" },
  { key: "cancelled", label: "任务取消" },
]

/** 默认全部展开，用户可按标题收起某一状态 */
export const TASK_STATUS_GROUPS_DEFAULT_OPEN: TaskStatusTone[] = TASK_STATUS_GROUPS.map(
  (g) => g.key,
)

export function taskStatusTone(status: string): TaskStatusTone {
  const key = (status || "").toLowerCase()
  if (key === "running") return "running"
  if (key === "completed" || key === "success") return "success"
  if (key === "failed") return "failed"
  if (key === "paused") return "paused"
  if (key === "cancelled") return "cancelled"
  return "pending"
}

export function taskStatusLabel(status: string): string {
  return TASK_STATUS_LABELS[(status || "").toLowerCase()] || status || "待执行"
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
