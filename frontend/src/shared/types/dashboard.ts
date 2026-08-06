/** Dashboard 模块共享类型 — 仪表盘统计数据、图表、活动日志 */

// ── 统计细分项 ──

export interface CaseBreakdownItem {
  type: string // 'ui_automation' | 'web_automation' | 'api_testing' | 'storage'
  total: number
  enabled: number
}

export interface ElementBreakdownItem {
  type: string // 'android' | 'web' | 'api'
  total: number
}

// ── 平台概览统计 ──

export interface DashboardStats {
  devices: { online: number; total: number; trend: number }
  cases: { total: number; enabled: number; trend: number; breakdown: CaseBreakdownItem[] }
  elements: { total: number; pages: number; breakdown: ElementBreakdownItem[]; typeBreakdown: ElementBreakdownItem[] }
  runs: { total: number; active: number; trend: number }
  agents: { total: number; active: number; trend: number }
  reports: { total: number }
  workflow: { total: number; page_flows: number; test_cases: number }
}

// ── 图表与摘要 ──

export interface ExecutionChart {
  labels: string[]
  success: number[]
  failed: number[]
  new_cases: number[]
}

export interface ExecutionSummary {
  passed: number
  failed: number
  new_cases_week: number
}

// ── 最近任务 ──

export interface RecentTask {
  id?: string | number
  task_id?: string
  run_id?: string
  status: string
  title?: string
  timestamp?: string
  passed?: number
  failed?: number
  total?: number
  time?: string
  cases?: { title: string; status: string; passed?: number; failed?: number }[]
}

// ── 活动时间线 ──

export interface ActivityItem {
  type: 'success' | 'warning' | 'error' | 'info'
  action: string
  time: string
  detail?: string
  tags?: string[]
}

// ── API 原始响应 ──

/** GET /api/dashboard/stats/ 返回的原始数据 */
export interface DashboardRawData {
  devices: { online: number; total: number; trend: number }
  cases: { total: number; enabled: number; trend: number; breakdown: CaseBreakdownItem[] }
  elements: { total: number; pages: number; breakdown: ElementBreakdownItem[]; type_breakdown: ElementBreakdownItem[] }
  runs: { total: number; active: number; trend: number }
  agents: { total: number; active: number; trend: number }
  reports: { total: number }
  workflow: { total: number; page_flows: number; test_cases: number }
  pass_rate: number
  charts: { execution: ExecutionChart }
  execution_summary: ExecutionSummary
  recent_tasks: RecentTask[]
  last_updated: string
  system_status: string
}

// ── 模板展示辅助 ──

export interface CaseBreakdownDisplay {
  type: string
  label: string
  color: string
  icon: object // component ref (Vue Component)
}

export interface ElementBreakdownDisplay {
  type: string
  label: string
  color: string
  icon: object // component ref (Vue Component)
}
