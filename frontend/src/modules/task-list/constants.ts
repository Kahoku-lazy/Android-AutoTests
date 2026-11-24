export function taskKindLabel(kind: string): string {
  if (kind === "assistant_sop") return "SOP"
  if (kind === "case_authoring") return "用例编写"
  return "设备执行"
}

export const TASK_DEVICE_POLL_INTERVAL_MS = 30000

export const CASE_SOURCE_PLATFORM = "platform"
export const CASE_SOURCE_YAML = "yaml"
export type CaseSource = typeof CASE_SOURCE_PLATFORM | typeof CASE_SOURCE_YAML

export const CASE_SOURCE_OPTIONS: { value: CaseSource; label: string; hint: string }[] = [
  { value: CASE_SOURCE_PLATFORM, label: "平台用例", hint: "选项目与用例，直接跑平台用例库" },
  { value: CASE_SOURCE_YAML, label: "本地 YAML", hint: "上传一份 YAML，可指定单条用例" },
]

export const CASE_SOURCE_DEFAULT: CaseSource = CASE_SOURCE_PLATFORM

export const TASK_REPORT_HEADER_ICON = "file-bar-chart"
export const TASK_REPORT_HEADER_GRADIENT = "linear-gradient(135deg,#999,#8b7f8f)"

export const TASK_REPORT_POLL_MS = 3000

export const TASK_PAGE_SIZE_OPTIONS = [10]
export const TASK_DEFAULT_PAGE_SIZE = 10

export const REPORT_POLL_BACKOFF_MS = [3000, 6000, 12000, 30000]

export const REPORT_POLL_MAX_FAILURES = 5

export const DEFAULT_OPEN_CASE_INDEX = 0

export const STEP_LOG_CHECK_TITLE = "日志检查"

export const STEP_LOG_CHECK_HINT = "本步断言需核对设备日志 · 取证窗 5 秒"

export const STEP_LOG_CHECK_NO_SHOT_TEXT = "该次点击后未截图"

export const STEP_EXEC_NO_SHOT_TEXT = "该步未截图"

export const AGENT_ROUTES = [{ value: "device_control", label: "控制设备" }] as const

export const ROUTE_LABELS: Record<string, string> = {
  device_control: "控制设备",
}

export const ROUTE_ICONS: Record<string, string> = {
  device_control: "📱",
}

export const TASK_FILTER_TABS = {
  all: { label: "全部任务" },
} as const

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

export const TASK_STATUS_GROUPS: { key: TaskStatusTone; label: string }[] = [
  { key: "pending", label: "待执行" },
  { key: "running", label: "执行中" },
  { key: "paused", label: "任务暂停" },
  { key: "success", label: "任务成功" },
  { key: "failed", label: "任务失败" },
  { key: "interrupted", label: "已中断" },
  { key: "cancelled", label: "任务取消" },
]

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

const RERUNNABLE_TONES = new Set<TaskStatusTone>(["success", "failed", "interrupted", "cancelled"])

const ORCHESTRATION_LABELS: Record<string, string> = {
  sop: "SOP",
  goal: "目标",
  team: "团队",
}

const KIND_LABELS: Record<string, string> = {
  ui_automation: "UI 自动化",
  case_authoring: "用例编写",
  requirement_breakdown: "需求拆解",
}

export function orchestrationLabel(value: string): string {
  return ORCHESTRATION_LABELS[value] || "—"
}

export function workflowKindLabel(value: string): string {
  return KIND_LABELS[value] || "—"
}

export function canRerunTask(status: string): boolean {
  return RERUNNABLE_TONES.has(taskStatusTone(status))
}
