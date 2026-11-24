export interface CaseBreakdownItem {
  project_id: number
  name: string
  total: number

  enabled?: number
}

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
  unpricedTokens: AiUsageMetric
  displayFx: { date: string; usdCny: string }
  archivedHourlyCost: number
  byRole: ByRoleMetric
  agents: AgentUsage[]
}

export interface UsageMetric {
  tokens: number
  cost: number
  calls: number
}

export interface UsageProvider extends UsageMetric {
  provider: string
}

export interface UsageCategory extends UsageMetric {
  category: string
  providers: UsageProvider[]
}

export interface UsageRecord {
  usage_id: string
  event_id: string
  execution_id: string
  occurred_at: string
  provider: string
  category: string
  model: string
  source: string
  tokens: number
  characters: number
  cost: string
  pricing_status: string
}

export interface UsageSummary {
  period: string
  total: UsageMetric
  categories: UsageCategory[]
  recent: UsageRecord[]
}

export interface UsageLedger {
  today: UsageSummary
  total: UsageSummary
  voiceToday: UsageSummary
  voiceTotal: UsageSummary
  recent: UsageRecord[]
}

export interface OpsCounts {
  users: number
  agents: number
  models: number
}

export interface DashboardStats {
  devices: { online: number; total: number }
  cases: { total: number; enabled: number; breakdown: CaseBreakdownItem[] }
  assistants: { total: number }
  workflows: { total: number }
  runs: { active: number; pending: number }

  ops: OpsCounts | null
  aiUsage: AiUsage
  usageLedger: UsageLedger
}

export interface ExecutionChart {
  labels: string[]
  success: number[]
  failed: number[]
}

export interface ModelDailySeries {
  name: string
  tokens: number[]
  cost: number[]
}

export interface AiTokenChart {
  labels: string[]
  totalTokens: number[]
  cacheTokens: number[]
  byModel: ModelDailySeries[]
  voiceByModel: ModelDailySeries[]
}

export interface DeepSeekCostChart {
  labels: string[]
  cost: number[]
}

export interface TodayUsageCurrent {
  hour: number
  tokens: number
  cost: number
}

export interface TodayUsageChart {
  tokens: (number | null)[]
  cost: (number | null)[]
  current: TodayUsageCurrent | null
}

export interface TodayUsageChartRaw {
  tokens: (number | null)[]
  cost: (number | null)[]
  current?: TodayUsageCurrent | null
}

export interface ModelDailySeriesRaw {
  name: string
  tokens: number[]
  cost: number[]
}

export interface AiTokenChartRaw {
  labels: string[]
  total_tokens: number[]
  cache_tokens: number[]
  by_model?: ModelDailySeriesRaw[]
  voice_by_model?: ModelDailySeriesRaw[]
}

export interface DeepSeekCostChartRaw {
  labels: string[]
  cost: number[]
}

export interface ExecutionSummary {
  passed: number
  failed: number
}

export interface RecentTask {
  id?: string | number
  task_id?: string
  run_id?: string
  status: string
  title?: string
  case_label?: string
  timestamp?: string
  passed?: number
  failed?: number
  total?: number
  time?: string
  cases?: { title: string; status: string; passed?: number; failed?: number }[]
}

export interface ActivityItem {
  type: string
  action: string
  time: string
  detail?: string
  tags?: string[]
}

export interface DashboardRawData {
  devices: { online: number; total: number }
  cases: { total: number; enabled: number; breakdown: CaseBreakdownItem[] }
  assistants?: { total: number }
  workflows?: { total: number }
  runs: { active: number; pending?: number }

  ops?: { users: number; agents: number; models: number }
  ai_usage: {
    task_count: AiUsageMetric
    input_tokens: AiUsageMetric
    output_tokens: AiUsageMetric
    total_tokens: AiUsageMetric
    cache_hit_tokens: AiUsageMetric
    cache_hit_rate: AiUsageMetric
    avg_tokens_per_task: AiUsageMetric
    deepseek_cost: AiUsageMetric
    unpriced_tokens?: AiUsageMetric
    display_fx?: { date: string; usd_cny: string }
    archived_hourly_cost?: number
    by_role: ByRoleMetric
    agents?: AgentUsage[]
  }
  charts: {
    execution: ExecutionChart
    ai_tokens: AiTokenChartRaw
    deepseek_cost: DeepSeekCostChartRaw

    today_usage?: TodayUsageChartRaw
  }
  execution_summary: ExecutionSummary
  recent_tasks: RecentTask[]
  last_updated: string
  system_status: string

  usage_ledger?: DashboardUsageLedgerRaw
}

export interface DashboardUsageLedgerRaw {
  today: UsageSummary
  total: UsageSummary
  voice_today: UsageSummary
  voice_total: UsageSummary
  recent: UsageRecord[]
}

export interface CaseProjectCardDisplay {
  projectId: number
  name: string
  total: number
  color: string
  path: string
}
