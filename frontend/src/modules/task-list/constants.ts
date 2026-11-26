export function taskKindLabel(kind: string): string {
  if (kind === "assistant_sop") return "SOP"
  if (kind === "case_authoring") return "用例编写"
  return "设备执行"
}

export const TASK_PAGE_SIZE_OPTIONS = [10]
export const TASK_DEFAULT_PAGE_SIZE = 10

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
