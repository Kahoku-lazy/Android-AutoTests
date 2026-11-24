/** 任务清单模块常量 — 任务状态 / 筛选 / 详情路由 */

/** 任务卡类型文案。未知类型回落设备执行，避免把 SOP 误标进去。 */
export function taskKindLabel(kind: string): string {
  if (kind === "assistant_sop") return "SOP"
  if (kind === "case_authoring") return "用例编写"
  return "设备执行"
}

/** 任务清单每页行数：单取值不渲染「显示行数」选择器（与设备管理页同口径） */
export const TASK_PAGE_SIZE_OPTIONS = [10]
export const TASK_DEFAULT_PAGE_SIZE = 10

/** 任务详情：执行侧「日志检查」区块（StepLogCheck）文案 */
export const STEP_LOG_CHECK_TITLE = "日志检查"

/** 本步带有需日志核对的断言时的说明（区块头部） */
export const STEP_LOG_CHECK_HINT = "本步断言需核对设备日志 · 取证窗 5 秒"

/** 某次点击之后确实没截图时如实标注 */
export const STEP_LOG_CHECK_NO_SHOT_TEXT = "该次点击后未截图"

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

/** 已经结束、可以再跑一次的状态。待执行和执行中不在此列。 */
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
