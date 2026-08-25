/** useDashboardStats — 仪表盘数据获取与状态管理 composable */
import { ref, type Ref } from 'vue'
import { fetchDashboardStats, fetchRecentActivities } from '../api'
import type {
  DashboardStats,
  ExecutionChart,
  ExecutionSummary,
  RecentTask,
  ActivityItem,
  DashboardRawData,
  AiUsage,
  AiUsageMetric,
} from '@/shared/types/dashboard'

// ── 返回类型接口 ──

export interface UseDashboardStatsReturn {
  loading: Ref<boolean>
  refreshing: Ref<boolean>
  error: Ref<string | null>
  stats: Ref<DashboardStats>
  executionChart: Ref<ExecutionChart>
  executionSummary: Ref<ExecutionSummary>
  recentTasks: Ref<RecentTask[]>
  lastUpdated: Ref<string>
  systemStatus: Ref<string>
  activities: Ref<ActivityItem[]>
  loadData: () => Promise<void>
  refreshData: () => Promise<void>
}

// ── 默认值 ──

const zeroMetric = (): AiUsageMetric => ({ today: 0, total: 0 })
const toMetric = (m?: AiUsageMetric): AiUsageMetric => m ?? zeroMetric()

const DEFAULT_AI_USAGE: AiUsage = {
  conversationCount: zeroMetric(),
  inputTokens: zeroMetric(),
  outputTokens: zeroMetric(),
  totalTokens: zeroMetric(),
  cacheHitTokens: zeroMetric(),
  cacheHitRate: zeroMetric(),
  avgTokensPerConversation: zeroMetric(),
}

const DEFAULT_STATS: DashboardStats = {
  devices: { online: 0, total: 0 },
  cases: { total: 0, enabled: 0, breakdown: [] },
  elements: { total: 0, pages: 0, typeBreakdown: [] },
  runs: { total: 0, active: 0 },
  agents: { total: 0, active: 0 },
  workflow: { total: 0 },
  aiUsage: DEFAULT_AI_USAGE,
}

const DEFAULT_CHART: ExecutionChart = { labels: [], success: [], failed: [] }
const DEFAULT_SUMMARY: ExecutionSummary = { passed: 0, failed: 0 }

// ── 映射函数 ──

interface MappedData {
  stats: DashboardStats
  executionChart: ExecutionChart
  executionSummary: ExecutionSummary
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
      elements: {
        total: raw.elements?.total ?? 0,
        pages: raw.elements?.pages ?? 0,
        typeBreakdown: raw.elements?.type_breakdown ?? [],
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
        conversationCount: toMetric(raw.ai_usage?.conversation_count),
        inputTokens: toMetric(raw.ai_usage?.input_tokens),
        outputTokens: toMetric(raw.ai_usage?.output_tokens),
        totalTokens: toMetric(raw.ai_usage?.total_tokens),
        cacheHitTokens: toMetric(raw.ai_usage?.cache_hit_tokens),
        cacheHitRate: toMetric(raw.ai_usage?.cache_hit_rate),
        avgTokensPerConversation: toMetric(raw.ai_usage?.avg_tokens_per_conversation),
      },
    },
    executionChart: raw.charts?.execution ?? DEFAULT_CHART,
    executionSummary: raw.execution_summary ?? DEFAULT_SUMMARY,
    recentTasks: raw.recent_tasks ?? [],
    lastUpdated: raw.last_updated ?? '',
    systemStatus: raw.system_status ?? 'normal',
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
  const recentTasks = ref<RecentTask[]>([])
  const lastUpdated = ref('')
  const systemStatus = ref('normal')
  const activities = ref<ActivityItem[]>([])

  async function _fetchAndMap(setLoadingFlag: (v: boolean) => void) {
    setLoadingFlag(true)
    error.value = null
    try {
      const [statsRes, activitiesRes] = await Promise.allSettled([
        fetchDashboardStats(),
        fetchRecentActivities(),
      ])

      if (statsRes.status === 'fulfilled') {
        const body = statsRes.value.data
        if (body?.status && body.data) {
          const mapped = mapStatsResponse(body.data)
          stats.value = mapped.stats
          executionChart.value = mapped.executionChart
          executionSummary.value = mapped.executionSummary
          recentTasks.value = mapped.recentTasks
          lastUpdated.value = mapped.lastUpdated
          systemStatus.value = mapped.systemStatus
        } else {
          error.value = body?.message || '统计数据加载失败，请检查网络连接'
        }
      } else {
        error.value = '统计数据加载失败，请检查网络连接'
      }

      if (activitiesRes.status === 'fulfilled') {
        const body = activitiesRes.value.data
        if (body?.status) {
          activities.value = body.data || []
        }
      } else {
        if (!error.value) error.value = '活动记录加载失败，请检查网络连接'
      }
    } catch (e: unknown) {
      error.value = '仪表盘数据加载失败，请稍后重试'
    } finally {
      setLoadingFlag(false)
    }
  }

  async function loadData() {
    await _fetchAndMap((v) => { loading.value = v })
  }

  async function refreshData() {
    await _fetchAndMap((v) => { refreshing.value = v })
  }

  return {
    loading,
    refreshing,
    error,
    stats,
    executionChart,
    executionSummary,
    recentTasks,
    lastUpdated,
    systemStatus,
    activities,
    loadData,
    refreshData,
  }
}
