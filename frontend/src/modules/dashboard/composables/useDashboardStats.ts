/** useDashboardStats — 仪表盘数据获取与状态管理 composable */
import { ref, type Ref } from "vue"
import { fetchDashboardStats, fetchRecentActivities } from "../api"
import type {
  DashboardStats,
  ExecutionChart,
  ExecutionSummary,
  RecentTask,
  ActivityItem,
  DashboardRawData,
  AiUsage,
  AiUsageMetric,
  AiTokenChart,
  DeepSeekCostChart,
  TodayUsageChart,
  UsageLedger,
  UsageSummary,
} from "@/shared/types/dashboard"

// ── 返回类型接口 ──

export interface UseDashboardStatsReturn {
  loading: Ref<boolean>
  refreshing: Ref<boolean>
  error: Ref<string | null>
  stats: Ref<DashboardStats>
  executionChart: Ref<ExecutionChart>
  executionSummary: Ref<ExecutionSummary>
  aiTokenChart: Ref<AiTokenChart>
  deepseekCostChart: Ref<DeepSeekCostChart>
  todayUsageChart: Ref<TodayUsageChart>
  recentTasks: Ref<RecentTask[]>
  lastUpdated: Ref<string>
  systemStatus: Ref<string>
  activities: Ref<ActivityItem[]>
  loadData: () => Promise<void>
  refreshData: () => Promise<void>
  /** 轮询用：刷新成功才写数据，不动 loading / refreshing，失败保留上次成功数据 */
  refreshSilently: () => Promise<void>
}

// ── 默认值 ──

const zeroMetric = (): AiUsageMetric => ({ today: 0, total: 0 })
const toMetric = (m?: AiUsageMetric): AiUsageMetric => m ?? zeroMetric()

const DEFAULT_AI_USAGE: AiUsage = {
  taskCount: zeroMetric(),
  inputTokens: zeroMetric(),
  outputTokens: zeroMetric(),
  totalTokens: zeroMetric(),
  cacheHitTokens: zeroMetric(),
  cacheHitRate: zeroMetric(),
  avgTokensPerTask: zeroMetric(),
  deepseekCost: zeroMetric(),
  byRole: { today: {}, total: {} },
  agents: [],
}

const emptyUsageSummary = (): UsageSummary => ({
  period: "today",
  total: { tokens: 0, cost: 0, calls: 0 },
  categories: [],
  recent: [],
})

const DEFAULT_USAGE_LEDGER: UsageLedger = {
  today: emptyUsageSummary(),
  total: { ...emptyUsageSummary(), period: "all" },
  voiceToday: emptyUsageSummary(),
  voiceTotal: { ...emptyUsageSummary(), period: "all" },
  recent: [],
}

const DEFAULT_STATS: DashboardStats = {
  devices: { online: 0, total: 0 },
  cases: { total: 0, enabled: 0, breakdown: [] },
  runs: { total: 0, active: 0 },
  agents: { total: 0, active: 0 },
  workflow: { total: 0 },
  aiUsage: DEFAULT_AI_USAGE,
  usageLedger: DEFAULT_USAGE_LEDGER,
}

const DEFAULT_CHART: ExecutionChart = { labels: [], success: [], failed: [] }
const DEFAULT_SUMMARY: ExecutionSummary = { passed: 0, failed: 0 }
const DEFAULT_AI_TOKEN_CHART: AiTokenChart = { labels: [], totalTokens: [], cacheTokens: [] }
const DEFAULT_DEEPSEEK_COST_CHART: DeepSeekCostChart = { labels: [], cost: [] }
const DEFAULT_TODAY_USAGE_CHART: TodayUsageChart = {
  tokens: [],
  cost: [],
  current: null,
}

// ── 映射函数 ──

interface MappedData {
  stats: DashboardStats
  executionChart: ExecutionChart
  executionSummary: ExecutionSummary
  aiTokenChart: AiTokenChart
  deepseekCostChart: DeepSeekCostChart
  todayUsageChart: TodayUsageChart
  recentTasks: RecentTask[]
  lastUpdated: string
  systemStatus: string
}

/** 将后端 API 响应映射为前端 dashboard 状态结构 */
export function mapStatsResponse(raw: DashboardRawData): MappedData {
  return {
    stats: {
      devices: {
        online: raw.devices?.online ?? 0,
        total: raw.devices?.total ?? 0,
      },
      cases: {
        total: raw.cases?.total ?? 0,
        enabled: raw.cases?.enabled ?? 0,
        breakdown: raw.cases?.breakdown ?? [],
      },
      runs: {
        total: raw.runs?.total ?? 0,
        active: raw.runs?.active ?? 0,
      },
      agents: {
        total: raw.agents?.total ?? 0,
        active: raw.agents?.active ?? 0,
      },
      workflow: { total: raw.workflow?.total ?? 0 },
      aiUsage: {
        taskCount: toMetric(raw.ai_usage?.task_count),
        inputTokens: toMetric(raw.ai_usage?.input_tokens),
        outputTokens: toMetric(raw.ai_usage?.output_tokens),
        totalTokens: toMetric(raw.ai_usage?.total_tokens),
        cacheHitTokens: toMetric(raw.ai_usage?.cache_hit_tokens),
        cacheHitRate: toMetric(raw.ai_usage?.cache_hit_rate),
        avgTokensPerTask: toMetric(raw.ai_usage?.avg_tokens_per_task),
        deepseekCost: toMetric(raw.ai_usage?.deepseek_cost),
        byRole: raw.ai_usage?.by_role ?? { today: {}, total: {} },
        agents: raw.ai_usage?.agents ?? [],
      },
      usageLedger: raw.usage_ledger
        ? {
            today: raw.usage_ledger.today,
            total: raw.usage_ledger.total,
            voiceToday: raw.usage_ledger.voice_today ?? emptyUsageSummary(),
            voiceTotal: raw.usage_ledger.voice_total ?? {
              ...emptyUsageSummary(),
              period: "all",
            },
            recent: raw.usage_ledger.recent,
          }
        : DEFAULT_USAGE_LEDGER,
    },
    executionChart: raw.charts?.execution ?? DEFAULT_CHART,
    executionSummary: raw.execution_summary ?? DEFAULT_SUMMARY,
    aiTokenChart: {
      labels: raw.charts?.ai_tokens?.labels ?? [],
      totalTokens: raw.charts?.ai_tokens?.total_tokens ?? [],
      cacheTokens: raw.charts?.ai_tokens?.cache_tokens ?? [],
    },
    deepseekCostChart: {
      labels: raw.charts?.deepseek_cost?.labels ?? [],
      cost: raw.charts?.deepseek_cost?.cost ?? [],
    },
    todayUsageChart: {
      tokens: raw.charts?.today_usage?.tokens ?? [],
      cost: raw.charts?.today_usage?.cost ?? [],
      current: raw.charts?.today_usage?.current ?? null,
    },
    recentTasks: raw.recent_tasks ?? [],
    lastUpdated: raw.last_updated ?? "",
    systemStatus: raw.system_status ?? "normal",
  }
}

// ── Composable ──

export function useDashboardStats(): UseDashboardStatsReturn {
  const loading = ref(true)
  const refreshing = ref(false)
  const error = ref<string | null>(null)

  const stats = ref<DashboardStats>({ ...DEFAULT_STATS })
  const executionChart = ref<ExecutionChart>({ ...DEFAULT_CHART })
  const executionSummary = ref<ExecutionSummary>({ ...DEFAULT_SUMMARY })
  const aiTokenChart = ref<AiTokenChart>({ ...DEFAULT_AI_TOKEN_CHART })
  const deepseekCostChart = ref<DeepSeekCostChart>({ ...DEFAULT_DEEPSEEK_COST_CHART })
  const todayUsageChart = ref<TodayUsageChart>({ ...DEFAULT_TODAY_USAGE_CHART })
  const recentTasks = ref<RecentTask[]>([])
  const lastUpdated = ref("")
  const systemStatus = ref("normal")
  const activities = ref<ActivityItem[]>([])

  async function _fetchAndMap(
    setLoadingFlag: (v: boolean) => void,
    options: { silent?: boolean } = {},
  ) {
    const silent = options.silent === true
    if (!silent) setLoadingFlag(true)
    if (!silent) error.value = null
    try {
      const [statsRes, activitiesRes] = await Promise.allSettled([
        fetchDashboardStats(),
        fetchRecentActivities(),
      ])

      if (statsRes.status === "fulfilled") {
        const body = statsRes.value.data
        if (body?.status && body.data) {
          const mapped = mapStatsResponse(body.data)
          stats.value = mapped.stats
          executionChart.value = mapped.executionChart
          executionSummary.value = mapped.executionSummary
          aiTokenChart.value = mapped.aiTokenChart
          deepseekCostChart.value = mapped.deepseekCostChart
          todayUsageChart.value = mapped.todayUsageChart
          recentTasks.value = mapped.recentTasks
          lastUpdated.value = mapped.lastUpdated
          systemStatus.value = mapped.systemStatus
          error.value = null
        } else if (!silent) {
          error.value = body?.message || "统计数据加载失败，请检查网络连接"
        }
      } else if (!silent) {
        error.value = "统计数据加载失败，请检查网络连接"
      }

      if (activitiesRes.status === "fulfilled") {
        const body = activitiesRes.value.data
        if (body?.status) {
          activities.value = body.data || []
        }
      } else if (!silent && !error.value) {
        error.value = "活动记录加载失败，请检查网络连接"
      }
    } catch (e: unknown) {
      // 静默轮询失败时保留上一次成功的数据，不把错误态盖到已展示的统计上
      if (!silent) error.value = "仪表盘数据加载失败，请稍后重试"
    } finally {
      if (!silent) setLoadingFlag(false)
    }
  }

  async function loadData() {
    await _fetchAndMap((v) => {
      loading.value = v
    })
  }

  async function refreshData() {
    await _fetchAndMap((v) => {
      refreshing.value = v
    })
  }

  async function refreshSilently() {
    await _fetchAndMap(() => {}, { silent: true })
  }

  return {
    loading,
    refreshing,
    error,
    stats,
    executionChart,
    executionSummary,
    aiTokenChart,
    deepseekCostChart,
    todayUsageChart,
    recentTasks,
    lastUpdated,
    systemStatus,
    activities,
    loadData,
    refreshData,
    refreshSilently,
  }
}
