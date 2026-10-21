/** Dashboard 模块共享类型 — 仪表盘统计数据、图表、活动日志 */

// ── 统计细分项 ──

export interface CaseBreakdownItem {
  project_id: number
  name: string
  total: number
  /** 文档用例无独立 enabled；有则与 total 同值 */
  enabled?: number
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

export interface AgentUsage {
  id: number
  name: string
  input_tokens: number
  output_tokens: number
  cache_hit_tokens: number
  cost_total: string
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
  agents: AgentUsage[]
}

export interface DashboardStats {
  devices: { online: number; total: number }
  cases: { total: number; enabled: number; breakdown: CaseBreakdownItem[] }
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

/** 进行中的那一小时：hour 为当前时刻（0–24） */
export interface TodayUsageCurrent {
  hour: number
  tokens: number
  cost: number
}

/** 当天逐小时用量：24 项，未走完/未开始的小时为 null，进行中小时在 current */
export interface TodayUsageChart {
  tokens: (number | null)[]
  cost: (number | null)[]
  current: TodayUsageCurrent | null
}

/** GET /api/dashboard/stats/ charts.today_usage 原始字段 */
export interface TodayUsageChartRaw {
  tokens: (number | null)[]
  cost: (number | null)[]
  current?: TodayUsageCurrent | null
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
    agents?: AgentUsage[]
  }
  charts: {
    execution: ExecutionChart
    ai_tokens: AiTokenChartRaw
    deepseek_cost: DeepSeekCostChartRaw
    /** 旧版接口无此字段时按空序列处理 */
    today_usage?: TodayUsageChartRaw
  }
  execution_summary: ExecutionSummary
  recent_tasks: RecentTask[]
  last_updated: string
  system_status: string
}

// ── 模板展示辅助 ──

export interface CaseProjectCardDisplay {
  projectId: number
  name: string
  total: number
  color: string
  path: string
}
