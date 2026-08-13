/**
 * [P1] 建议测 — DashboardView.logic 编排层
 * 数据获取已在 P0 覆盖；这里测编排独有行为（挂载自动加载、分项查询回退、展示配置）。
 * 目录：tests/dashboard/p1/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { fetchDashboardStats, fetchRecentActivities } from '@/modules/dashboard/api'
import { useDashboardView } from '@/modules/dashboard/DashboardView.logic'
import { mountComposable } from '../../helpers/mountComposable'
import type { DashboardRawData } from '@/shared/types/dashboard'

vi.mock('@/modules/dashboard/api', () => ({
  fetchDashboardStats: vi.fn(),
  fetchRecentActivities: vi.fn(),
}))

function makeRaw(): DashboardRawData {
  return {
    devices: { online: 3, total: 5, trend: 0 },
    cases: {
      total: 20,
      enabled: 18,
      trend: 4,
      breakdown: [
        { type: 'ui_automation', total: 8, enabled: 7 },
        { type: 'api_testing', total: 4, enabled: 4 },
      ],
    },
    elements: {
      total: 42,
      pages: 6,
      breakdown: [],
      type_breakdown: [
        { type: 'android', total: 30 },
        { type: 'web', total: 12 },
      ],
    },
    runs: { total: 100, active: 2, trend: 0 },
    agents: { total: 4, active: 1, trend: 0 },
    reports: { total: 9 },
    workflow: { total: 7, page_flows: 3, test_cases: 4 },
    pass_rate: 0.95,
    charts: { execution: { labels: [], success: [], failed: [], new_cases: [] } },
    execution_summary: { passed: 0, failed: 0, new_cases_week: 0 },
    recent_tasks: [],
    last_updated: '',
    system_status: 'normal',
  }
}

async function mountView(raw: DashboardRawData = makeRaw()) {
  vi.mocked(fetchDashboardStats).mockResolvedValue({
    data: { status: true, data: raw },
  } as never)
  vi.mocked(fetchRecentActivities).mockResolvedValue({
    data: { status: true, data: [] },
  } as never)

  const { result } = await mountComposable(() => useDashboardView())
  await flushPromises()
  return result
}

describe('[P1] useDashboardView（编排）', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('挂载时自动 loadData，数据进入 stats', async () => {
    const result = await mountView()

    expect(fetchDashboardStats).toHaveBeenCalledTimes(1)
    expect(result.stats.value.devices.online).toBe(3)
    expect(result.loading.value).toBe(false)
  })

  it('getBreakdownItem 命中：返回对应 breakdown 项', async () => {
    const result = await mountView()

    expect(result.getBreakdownItem('api_testing')).toEqual({
      type: 'api_testing',
      total: 4,
      enabled: 4,
    })
  })

  it('getBreakdownItem 未命中：回退零值项', async () => {
    const result = await mountView()

    expect(result.getBreakdownItem('storage')).toEqual({
      type: 'storage',
      total: 0,
      enabled: 0,
    })
  })

  it('getElementItem 命中：返回 typeBreakdown 项', async () => {
    const result = await mountView()

    expect(result.getElementItem('web')).toEqual({ type: 'web', total: 12 })
  })

  it('getElementItem 未命中：回退零值项', async () => {
    const result = await mountView()

    expect(result.getElementItem('api')).toEqual({ type: 'api', total: 0 })
  })

  it('暴露展示配置：页头与四类用例 / 三类元素', () => {
    // 展示配置为静态导出，直接断言（无需挂载）
    return mountView().then((result) => {
      expect(result.PAGE_HEADER.title).toBe('仪表盘')
      expect(result.caseBreakdown).toHaveLength(4)
      expect(result.caseBreakdown.map((c) => c.type)).toEqual([
        'ui_automation',
        'web_automation',
        'api_testing',
        'storage',
      ])
      expect(result.elementBreakdown).toHaveLength(3)
      expect(result.elementBreakdown.map((e) => e.type)).toEqual(['android', 'web', 'api'])
    })
  })
})
