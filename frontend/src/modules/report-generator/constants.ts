/**
 * report-generator 模块常量 — 测试报告台账
 *
 * 列定义、筛选、文案与分页的唯一真相源；色值一律取 tokens.css 令牌。
 */

// ── 页头配置 ──
export const PAGE_HEADER = {
  title: "测试报告",
  subtitle: "任务与助手对话执行完成后生成的报告台账",
  icon: "file-bar-chart",
  iconGradient: "linear-gradient(135deg, var(--c-report), var(--c-ai))",
}

// ── 来源筛选（count 由 summary 提供）──
export const SOURCE_TABS = [
  { key: "all", label: "全部" },
  { key: "sop", label: "SOP" },
  { key: "agent", label: "智能体" },
] as const

export const SOURCE_LABELS: Record<string, string> = {
  sop: "SOP",
  agent: "智能体",
}

// ── 表格列定义 ──
export const TABLE_COLUMNS = [
  { title: "来源", dataIndex: "source", icon: "🧭", width: 110, align: "center" },
  { title: "用例 / 助手", dataIndex: "identity", icon: "🏷", minWidth: 240 },
  { title: "关联", dataIndex: "relation", icon: "🔗", width: 170 },
  { title: "结果摘要", dataIndex: "outcome", icon: "🚦", minWidth: 200 },
  { title: "生成时间", dataIndex: "moment", icon: "🕒", width: 170 },
  { title: "操作", dataIndex: "actions", icon: "💬", width: 132, align: "center" },
]

// ── SOP 终态标签（台账只收录已完成报告，只有这两类）──
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

// ── 分页与去抖 ──
export const PAGE_SIZE_OPTIONS = [10, 20, 50]
export const FILTER_DEBOUNCE = 350

// ── 文案 ──
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

// ── 纯函数：来源与状态展示 ──
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
