/** BUG 单管理常量 — 分类、状态、列定义、文案与路由的唯一真相源 */
import type { BugCategory, BugStatus } from "./types"

export const BUG_PAGE_HEADER = {
  title: "BUG单管理",
  subtitle: "任务清单里的错误集中登记：UI 自动化与测试用例编写分开追踪",
  icon: "bug",
  iconGradient: "linear-gradient(135deg, var(--c-runner), var(--c-report))",
}

export const BUG_CATEGORY_LABELS: Record<BugCategory, string> = {
  ui_automation: "UI 自动化",
  case_authoring: "测试用例编写",
}

export const BUG_STATUS_LABELS: Record<BugStatus, string> = {
  open: "待处理",
  resolved: "已解决",
  ignored: "已忽略",
}

export const BUG_STATUS_OPTIONS: { value: BugStatus; label: string }[] = [
  { value: "open", label: BUG_STATUS_LABELS.open },
  { value: "resolved", label: BUG_STATUS_LABELS.resolved },
  { value: "ignored", label: BUG_STATUS_LABELS.ignored },
]

export const BUG_TASK_STATUS_LABELS: Record<string, string> = {
  failed: "任务失败",
  interrupted: "已中断",
  completed: "已完成",
  cancelled: "已取消",
  running: "执行中",
  pending: "待执行",
}

export const BUG_CATEGORY_TABS = [
  { key: "all", label: "全部 BUG" },
  { key: "ui_automation", label: "UI 自动化" },
  { key: "case_authoring", label: "测试用例编写" },
] as const

export const BUG_TABLE_COLUMNS = [
  { title: "BUG 编号", dataIndex: "bug_no", width: 118 },
  { title: "分类", dataIndex: "category", width: 120, align: "center" },
  { title: "标题", dataIndex: "title", minWidth: 260 },
  { title: "关联任务", dataIndex: "task_id", width: 104, align: "center" },
  { title: "状态", dataIndex: "status", width: 96, align: "center" },
  { title: "创建时间", dataIndex: "created_at", width: 150 },
  { title: "操作", dataIndex: "actions", width: 78, align: "center" },
]

export const BUG_PAGE_SIZE_OPTIONS = [10, 20, 50]

export const BUG_KEYWORD_PLACEHOLDER = "搜索 BUG 标题 / 任务编号 / BUG 编号"
export const BUG_STATUS_PLACEHOLDER = "全部状态"

export const BUG_EMPTY_TEXT = {
  noData: "暂无 BUG 单",
  hint: "失败任务会自动登记；历史任务可点「同步历史错误」补录",
}

export const BUG_SYNC = {
  running: "同步中…",
  empty: "没有新的历史错误",
  done: "历史错误已同步",
}

export function bugStatusClass(status: string): string {
  return `is-${status || "open"}`
}

export function bugCategoryClass(category: string): string {
  return category === "case_authoring" ? "is-case" : "is-ui"
}

export function bugTaskRoute(taskId: number | string): string {
  return `/tasks/${taskId}`
}

export function bugTaskStatusLabel(status: string): string {
  return BUG_TASK_STATUS_LABELS[status] || status || "—"
}

export function formatBugTime(iso: string): string {
  if (!iso) return "—"
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}
