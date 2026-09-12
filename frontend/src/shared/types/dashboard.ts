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

export interface AiUsageMetric {
  today: number
  total: number
}

export interface RoleTokenUsage {
  input_tokens: number
  output_tokens: number
  cache_input_tokens: number
}

export interface ByRoleMetric {
  today: Record<string, RoleTokenUsage>
  total: Record<string, RoleTokenUsage>
}

export interface AiUsage {
  taskCount: AiUsageMetric
  inputTokens: AiUsageMetric
  outputTokens: AiUsageMetric
  totalTokens: AiUsageMetric
  cacheHitTokens: AiUsageMetric
  cacheHitRate: AiUsageMetric
  avgTokensPerTask: AiUsageMetric
  deepseekCost: AiUsageMetric
  byRole: ByRoleMetric
}

export interface DashboardStats {
  devices: { online: number; total: number }
  cases: { total: number; enabled: number; breakdown: CaseBreakdownItem[] }
  elements: { total: number; pages: number; typeBreakdown: ElementBreakdownItem[] }
  runs: { total: number; active: number }
  agents: { total: number; active: number }
  workflow: { total: number }
  aiUsage: AiUsage
}

// ── 图表与摘要 ──

export interface ExecutionChart {
  labels: string[]
  success: number[]
  failed: number[]
}

export interface AiTokenChart {
  labels: string[]
  totalTokens: number[]
  cacheTokens: number[]
}

export interface DeepSeekCostChart {
  labels: string[]
  cost: number[]
}

/** GET /api/dashboard/stats/ charts.ai_tokens 原始 snake_case 字段 */
export interface AiTokenChartRaw {
  labels: string[]
  total_tokens: number[]
  cache_tokens: number[]
}

/** GET /api/dashboard/stats/ charts.deepseek_cost 原始字段 */
export interface DeepSeekCostChartRaw {
  labels: string[]
  cost: number[]
}

export interface ExecutionSummary {
  passed: number
  failed: number
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
  type: string // 'run' | 'agent'，枚举外值按默认样式展示（PRD §2.3）
  action: string
  time: string
  detail?: string
  tags?: string[]
}

// ── API 原始响应 ──

/** GET /api/dashboard/stats/ 返回的原始数据 */
export interface DashboardRawData {
  devices: { online: number; total: number }
  cases: { total: number; enabled: number; breakdown: CaseBreakdownItem[] }
  elements: { total: number; pages: number; type_breakdown: ElementBreakdownItem[] }
  runs: { total: number; active: number }
  agents: { total: number; active: number }
  workflow: { total: number }
  ai_usage: {
    task_count: AiUsageMetric
    input_tokens: AiUsageMetric
    output_tokens: AiUsageMetric
    total_tokens: AiUsageMetric
    cache_hit_tokens: AiUsageMetric
    cache_hit_rate: AiUsageMetric
    avg_tokens_per_task: AiUsageMetric
    deepseek_cost: AiUsageMetric
    by_role: ByRoleMetric
  }
  charts: {
    execution: ExecutionChart
    ai_tokens: AiTokenChartRaw
    deepseek_cost: DeepSeekCostChartRaw
  }
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
