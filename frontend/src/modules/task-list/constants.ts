/** 任务清单模块常量 — 任务状态 / 筛选 / 详情路由 */

/** 新建任务设备下拉轮询间隔，与设备管理 HEARTBEAT_INTERVAL（30s）对齐 */
export const TASK_DEVICE_POLL_INTERVAL_MS = 30000

/** 用例来源：平台用例库直接执行，或上传本地 YAML */
export const CASE_SOURCE_PLATFORM = "platform"
export const CASE_SOURCE_YAML = "yaml"
export type CaseSource = typeof CASE_SOURCE_PLATFORM | typeof CASE_SOURCE_YAML

/** 用例来源选项（弹窗单选） */
export const CASE_SOURCE_OPTIONS: { value: CaseSource; label: string; hint: string }[] = [
  { value: CASE_SOURCE_PLATFORM, label: "平台用例", hint: "选项目与用例，直接跑平台用例库" },
  { value: CASE_SOURCE_YAML, label: "本地 YAML", hint: "上传一份 YAML，可指定单条用例" },
]

/** 默认用例来源：平台用例 */
export const CASE_SOURCE_DEFAULT: CaseSource = CASE_SOURCE_PLATFORM

/** 任务详情页页头图标与渐变 */
export const TASK_REPORT_HEADER_ICON = "file-bar-chart"
export const TASK_REPORT_HEADER_GRADIENT = "linear-gradient(135deg,#999,#8b7f8f)"

/** 任务详情：运行中任务（执行类与用例编写类）的报告自动刷新间隔；<=0 视为关闭自动刷新 */
export const TASK_REPORT_POLL_MS = 3000

/** 任务详情：自动刷新连续失败时的退避序列（末项封顶） */
export const REPORT_POLL_BACKOFF_MS = [3000, 6000, 12000, 30000]

/** 任务详情：允许的连续失败次数；超过该次数（即第 6 次失败）停止自动刷新，改为手动重试 */
export const REPORT_POLL_MAX_FAILURES = 5

/** 任务详情：默认只展开第一个用例 */
export const DEFAULT_OPEN_CASE_INDEX = 0

/** 任务详情全屏页 */
export function taskDetailRoute(id: number | string): string {
  return `/tasks/${id}`
}

/** 任务详情：执行侧「日志检查」区块（StepLogCheck）文案 */
export const STEP_LOG_CHECK_TITLE = "日志检查"

/** 本步带有需日志核对的断言时的说明（区块头部） */
export const STEP_LOG_CHECK_HINT = "本步断言需核对设备日志 · 取证窗 5 秒"

/** 某次点击之后确实没截图时如实标注 */
export const STEP_LOG_CHECK_NO_SHOT_TEXT = "该次点击后未截图"

/** 任务详情：执行结果段里本步没有截图时如实标注（新执行契约的 screenshot 为空串） */
export const STEP_EXEC_NO_SHOT_TEXT = "该步未截图"

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

/** 任务卡片七态（待执行 / 执行中 / 任务成功 / 任务失败 / 已中断 / 任务取消 / 任务暂停） */
export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: "待执行",
  running: "执行中",
  completed: "任务成功",
  success: "任务成功",
  failed: "任务失败",
  interrupted: "已中断",
  cancelled: "任务取消",
  paused: "任务暂停",
}

export type TaskStatusTone =
  "pending" | "running" | "success" | "failed" | "interrupted" | "cancelled" | "paused"

/** 任务看板按状态分组的展示顺序（completed/success 合并为「任务成功」） */
export const TASK_STATUS_GROUPS: { key: TaskStatusTone; label: string }[] = [
  { key: "pending", label: "待执行" },
  { key: "running", label: "执行中" },
  { key: "paused", label: "任务暂停" },
  { key: "success", label: "任务成功" },
  { key: "failed", label: "任务失败" },
  { key: "interrupted", label: "已中断" },
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
  if (key === "interrupted") return "interrupted"
  if (key === "paused") return "paused"
  if (key === "cancelled") return "cancelled"
  return "pending"
}

export function taskStatusLabel(status: string): string {
  return TASK_STATUS_LABELS[(status || "").toLowerCase()] || status || "待执行"
}
