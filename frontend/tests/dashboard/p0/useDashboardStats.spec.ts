/**
 * [P0] 必测 — 仪表盘数据获取与映射（mock 后端，不断真网络）
 * 目录：tests/dashboard/p0/
 *
 * useDashboardStats：loading/refreshing/error 状态 + 双接口编排。
 * mapStatsResponse：纯映射函数，覆盖完整数据与缺字段回退。
 */
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { fetchDashboardStats, fetchRecentActivities } from '@/modules/dashboard/api'
import { mapStatsResponse, useDashboardStats } from '@/modules/dashboard/composables/useDashboardStats'
import type { DashboardRawData } from '@/shared/types/dashboard'

vi.mock('@/modules/dashboard/api', () => ({
  fetchDashboardStats: vi.fn(),
  fetchRecentActivities: vi.fn(),
}))

function makeRaw(): DashboardRawData {
  return {
    devices: { online: 3, total: 5, trend: 12 },
    cases: {
      total: 20,
      enabled: 18,
      trend: 4,
      breakdown: [{ type: 'ui_automation', total: 8, enabled: 7 }],
    },
    elements: {
      total: 42,
      pages: 6,
      breakdown: [{ type: 'android', total: 30 }],
      type_breakdown: [{ type: 'android', total: 30 }],
    },
    runs: { total: 100, active: 2, trend: -5 },
    agents: { total: 4, active: 1, trend: 0 },
    reports: { total: 9 },
    workflow: { total: 7, page_flows: 3, test_cases: 4 },
    pass_rate: 0.95,
    charts: {
      execution: { labels: ['W1'], success: [10], failed: [2], new_cases: [5] },
    },
    execution_summary: { passed: 50, failed: 3, new_cases_week: 6 },
    recent_tasks: [{ id: 'r1', status: 'success', title: '冒烟' }],
    last_updated: '2026-08-13 10:00',
    system_status: 'no_device',
  }
}

function makeStatsRes(status: boolean, data: DashboardRawData) {
  return { data: { status, data } }
}

describe('[P0] useDashboardStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(fetchDashboardStats).mockResolvedValue(makeStatsRes(true, makeRaw()) as never)
    vi.mocked(fetchRecentActivities).mockResolvedValue({
      data: {
        status: true,
        data: [{ type: 'success', action: '执行完成', time: '10:00' }],
      },
    } as never)
  })

  it('loadData 成功：映射全部字段，loading 结束，无 error', async () => {
    const s = useDashboardStats()
    expect(s.loading.value).toBe(true)

    await s.loadData()

    expect(s.loading.value).toBe(false)
    expect(s.error.value).toBeNull()
    expect(s.stats.value.devices).toEqual({ online: 3, total: 5, trend: 12 })
    expect(s.stats.value.cases.breakdown).toHaveLength(1)
    expect(s.stats.value.elements.typeBreakdown).toEqual([{ type: 'android', total: 30 }])
    expect(s.stats.value.runs.active).toBe(2)
    expect(s.stats.value.agents.total).toBe(4)
    expect(s.stats.value.reports.total).toBe(9)
    expect(s.stats.value.workflow).toEqual({ total: 7, page_flows: 3, test_cases: 4 })
    expect(s.executionChart.value.labels).toEqual(['W1'])
    expect(s.executionSummary.value).toEqual({ passed: 50, failed: 3, new_cases_week: 6 })
    expect(s.recentTasks.value).toHaveLength(1)
    expect(s.lastUpdated.value).toBe('2026-08-13 10:00')
    expect(s.systemStatus.value).toBe('no_device')
    expect(s.activities.value).toHaveLength(1)
  })

  it('stats 接口业务失败：写入后端 message', async () => {
    vi.mocked(fetchDashboardStats).mockResolvedValue({
      data: { status: false, message: '服务端统计暂不可用' },
    } as never)

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBe('服务端统计暂不可用')
    expect(s.stats.value.devices.total).toBe(0)
  })

  it('stats 请求抛错：写入网络错误文案', async () => {
    vi.mocked(fetchDashboardStats).mockRejectedValue(new Error('boom'))

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBe('统计数据加载失败，请检查网络连接')
  })

  it('stats 成功 + activities 抛错：error 为活动加载失败', async () => {
    vi.mocked(fetchRecentActivities).mockRejectedValue(new Error('boom'))

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBe('活动记录加载失败，请检查网络连接')
    expect(s.activities.value).toEqual([])
  })

  it('stats 失败 + activities 抛错：error 保持 stats 的错误，不被覆盖', async () => {
    vi.mocked(fetchDashboardStats).mockResolvedValue({
      data: { status: false, message: '服务端统计暂不可用' },
    } as never)
    vi.mocked(fetchRecentActivities).mockRejectedValue(new Error('boom'))

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBe('服务端统计暂不可用')
  })

  it('activities 业务失败：activities 保持空数组', async () => {
    vi.mocked(fetchRecentActivities).mockResolvedValue({
      data: { status: false, message: '无活动' },
    } as never)

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBeNull()
    expect(s.activities.value).toEqual([])
  })

  it('响应形状异常（无 data）：整体兜底错误', async () => {
    vi.mocked(fetchDashboardStats).mockResolvedValue(undefined as never)

    const s = useDashboardStats()
    await s.loadData()

    expect(s.error.value).toBe('仪表盘数据加载失败，请稍后重试')
  })

  it('refreshData：置 refreshing，结束后复位并更新数据', async () => {
    let resolveStats!: (v: unknown) => void
    vi.mocked(fetchDashboardStats).mockReturnValue(
      new Promise((r) => { resolveStats = r }) as never,
    )
    vi.mocked(fetchRecentActivities).mockResolvedValue({
      data: { status: true, data: [] },
    } as never)

    const s = useDashboardStats()
    const p = s.refreshData()
    expect(s.refreshing.value).toBe(true)

    resolveStats(makeStatsRes(true, makeRaw()))
    await p

    expect(s.refreshing.value).toBe(false)
    expect(s.stats.value.devices.online).toBe(3)
  })
})

describe('[P0] mapStatsResponse（纯映射）', () => {
  it('完整数据逐字段映射', () => {
    const mapped = mapStatsResponse(makeRaw())

    expect(mapped.stats.devices).toEqual({ online: 3, total: 5, trend: 12 })
    expect(mapped.stats.cases).toEqual({
      total: 20,
      enabled: 18,
      trend: 4,
      breakdown: [{ type: 'ui_automation', total: 8, enabled: 7 }],
    })
    expect(mapped.stats.elements.typeBreakdown).toEqual([{ type: 'android', total: 30 }])
    expect(mapped.stats.workflow).toEqual({ total: 7, page_flows: 3, test_cases: 4 })
    expect(mapped.executionChart.success).toEqual([10])
    expect(mapped.executionSummary.passed).toBe(50)
    expect(mapped.recentTasks).toHaveLength(1)
    expect(mapped.lastUpdated).toBe('2026-08-13 10:00')
    expect(mapped.systemStatus).toBe('no_device')
  })

  it('空对象：全部回退默认值', () => {
    const mapped = mapStatsResponse({} as DashboardRawData)

    expect(mapped.stats.devices).toEqual({ online: 0, total: 0, trend: 0 })
    expect(mapped.stats.cases.breakdown).toEqual([])
    expect(mapped.stats.elements.typeBreakdown).toEqual([])
    expect(mapped.stats.workflow).toEqual({ total: 0, page_flows: 0, test_cases: 0 })
    expect(mapped.executionChart).toEqual({ labels: [], success: [], failed: [], new_cases: [] })
    expect(mapped.executionSummary).toEqual({ passed: 0, failed: 0, new_cases_week: 0 })
    expect(mapped.recentTasks).toEqual([])
    expect(mapped.lastUpdated).toBe('')
    expect(mapped.systemStatus).toBe('normal')
  })

  it('部分字段缺失：缺失项回退，存在项保留', () => {
    const mapped = mapStatsResponse({
      devices: { online: 2, total: 4 },
      runs: { total: 10, active: 1, trend: 3 },
    } as DashboardRawData)

    expect(mapped.stats.devices.trend).toBe(0)
    expect(mapped.stats.devices.online).toBe(2)
    expect(mapped.stats.runs.trend).toBe(3)
    expect(mapped.stats.cases).toEqual({
      total: 0, enabled: 0, trend: 0, breakdown: [],
    })
    expect(mapped.executionChart.labels).toEqual([])
    expect(mapped.systemStatus).toBe('normal')
  })
})
