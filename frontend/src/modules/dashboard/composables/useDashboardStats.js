import { ref } from 'vue'
import { fetchDashboardStats, fetchRecentActivities } from '../api.js'

/**
 * 将后端 API 响应映射为前端 dashboard 状态结构。
 * 所有字段提供 nullish coalescing 默认值，确保 API 缺字段时 UI 不崩溃。
 */
export function mapStatsResponse(d) {
  return {
    stats: {
      devices: {
        online: d.devices?.online ?? 0,
        total: d.devices?.total ?? 0,
        trend: d.devices?.trend ?? 0,
      },
      cases: {
        total: d.cases?.total ?? 0,
        enabled: d.cases?.enabled ?? 0,
        trend: d.cases?.trend ?? 0,
        breakdown: d.cases?.breakdown ?? [],
      },
      elements: {
        total: d.elements?.total ?? 0,
        pages: d.elements?.pages ?? 0,
        breakdown: d.elements?.breakdown ?? [],
        typeBreakdown: d.elements?.type_breakdown ?? [],
      },
      runs: {
        total: d.runs?.total ?? 0,
        active: d.runs?.active ?? 0,
        trend: d.runs?.trend ?? 0,
      },
      agents: {
        total: d.agents?.total ?? 0,
        active: d.agents?.active ?? 0,
        trend: d.agents?.trend ?? 0,
      },
      reports: { total: d.reports?.total ?? 0 },
      workflow: d.workflow ?? { total: 0, page_flows: 0, test_cases: 0 },
    },
    passRate: d.pass_rate ?? 0,
    executionChart: d.charts?.execution ?? {
      labels: [],
      success: [],
      failed: [],
      new_cases: [],
    },
    executionSummary: d.execution_summary ?? {
      passed: 0,
      failed: 0,
      new_cases_week: 0,
    },
    recentTasks: d.recent_tasks ?? [],
    lastUpdated: d.last_updated ?? '',
    systemStatus: d.system_status ?? 'normal',
  }
}

/**
 * Dashboard 数据获取与状态管理 composable。
 *
 * 返回:
 *   loading, refreshing, error — UI 三态
 *   stats, passRate, executionChart, executionSummary,
 *   recentTasks, lastUpdated, systemStatus, activities — 业务数据
 *   loadData(), refreshData() — 获取/刷新方法
 */
export function useDashboardStats() {
  const loading = ref(true)
  const refreshing = ref(false)
  const error = ref(null)

  const stats = ref({
    devices: { online: 0, total: 0, trend: 0 },
    cases: { total: 0, enabled: 0, trend: 0, breakdown: [] },
    elements: { total: 0, pages: 0, breakdown: [], typeBreakdown: [] },
    runs: { total: 0, active: 0, trend: 0 },
    agents: { total: 0, active: 0, trend: 0 },
    reports: { total: 0 },
    workflow: { total: 0, page_flows: 0, test_cases: 0 },
  })
  const passRate = ref(0)
  const executionChart = ref({ labels: [], success: [], failed: [], new_cases: [] })
  const executionSummary = ref({ passed: 0, failed: 0, new_cases_week: 0 })
  const recentTasks = ref([])
  const lastUpdated = ref('')
  const systemStatus = ref('normal')
  const activities = ref([])

  async function _fetchAndMap(setLoadingFlag) {
    setLoadingFlag(true)
    error.value = null
    try {
      const [statsRes, activitiesRes] = await Promise.allSettled([
        fetchDashboardStats(),
        fetchRecentActivities(),
      ])

      if (statsRes.status === 'fulfilled') {
        if (statsRes.value.data?.ok) {
          const mapped = mapStatsResponse(statsRes.value.data.data)
          stats.value = mapped.stats
          passRate.value = mapped.passRate
          executionChart.value = mapped.executionChart
          executionSummary.value = mapped.executionSummary
          recentTasks.value = mapped.recentTasks
          lastUpdated.value = mapped.lastUpdated
          systemStatus.value = mapped.systemStatus
        } else {
          error.value = statsRes.value.data?.error || '统计数据加载失败，请检查网络连接'
        }
      } else {
        error.value = '统计数据加载失败，请检查网络连接'
      }

      if (activitiesRes.status === 'fulfilled') {
        if (activitiesRes.value.data?.ok) {
          activities.value = activitiesRes.value.data.data || []
        }
      } else {
        if (!error.value) error.value = '活动记录加载失败，请检查网络连接'
      }
    } catch (e) {
      error.value = e.message || '仪表盘数据加载失败'
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
    passRate,
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
