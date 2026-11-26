export const PAGE_HEADER = {
  title: "测试报告",
  subtitle: "任务与助手对话执行完成后生成的报告台账",
  icon: "file-bar-chart",
  iconGradient: "linear-gradient(135deg, var(--c-report), var(--c-ai))",
}

export const SOURCE_TABS = [
  { key: "all", label: "全部" },
  { key: "sop", label: "SOP" },
  { key: "agent", label: "智能体" },
] as const

export const SOURCE_LABELS: Record<string, string> = {
  sop: "SOP",
  agent: "智能体",
}

export const TABLE_COLUMNS = [
  { title: "来源", dataIndex: "source", icon: "🧭", width: 110, align: "center" },
  { title: "用例 / 助手", dataIndex: "identity", icon: "🏷", minWidth: 240 },
  { title: "关联", dataIndex: "relation", icon: "🔗", width: 170 },
  { title: "结果摘要", dataIndex: "outcome", icon: "🚦", minWidth: 200 },
  { title: "生成时间", dataIndex: "moment", icon: "🕒", width: 170 },
  { title: "操作", dataIndex: "actions", icon: "💬", width: 132, align: "center" },
]

export const SOP_STATUS_LABELS: Record<string, string> = {
  completed: "通过",
  success: "通过",
  failed: "失败",
}

export const SOP_STATUS_CLASS: Record<string, string> = {
  completed: "is-pass",
  success: "is-pass",
  failed: "is-fail",
}

export const PAGE_SIZE_OPTIONS = [10, 20, 50]
export const FILTER_DEBOUNCE = 350

export const KEYWORD_PLACEHOLDER = "搜索用例名称 / 任务 ID / 助手名称或编号"
export const EMPTY_TEXT = {
  noData: "暂无报告",
  hint: "报告在执行完成后生成：去任务清单发布任务，或在平台助手跑一轮对话",
}
export const REPORT_MESSAGES = {
  missing: "报告不存在",
  openFailed: "报告打开失败",
  loadFailed: "加载报告失败，请检查服务状态",
}

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] || source
}

export function sourceClass(source: string): string {
  return source === "agent" ? "is-agent" : "is-sop"
}

export function sopStatusLabel(status: string): string {
  return SOP_STATUS_LABELS[status] || status || "—"
}

export function sopStatusClass(status: string): string {
  return SOP_STATUS_CLASS[status] || "is-fail"
}
