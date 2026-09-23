/**
 * [P1] 建议测 — DashboardView.logic 编排层
 * 数据获取已在 P0 覆盖；这里测编排独有行为（挂载自动加载、项目卡映射、元素分项）。
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

/** AI 用量本文件不参与断言：零值补齐 DashboardRawData 的必填字段 */
const ZERO_METRIC = { today: 0, total: 0 }
const ZERO_AI_USAGE: DashboardRawData['ai_usage'] = {
  task_count: ZERO_METRIC,
  input_tokens: ZERO_METRIC,
  output_tokens: ZERO_METRIC,
  total_tokens: ZERO_METRIC,
  cache_hit_tokens: ZERO_METRIC,
  cache_hit_rate: ZERO_METRIC,
  avg_tokens_per_task: ZERO_METRIC,
  deepseek_cost: ZERO_METRIC,
  by_role: { today: {}, total: {} },
}

function makeRaw(): DashboardRawData {
  return {
    devices: { online: 3, total: 5 },
    cases: {
      total: 12,
      enabled: 12,
      breakdown: [
        { project_id: 10, name: '家电冒烟', total: 8 },
        { project_id: 11, name: '空项目', total: 0 },
      ],
    },
    elements: {
      total: 42,
      pages: 6,
      type_breakdown: [
        { type: 'android', total: 30 },
        { type: 'web', total: 12 },
      ],
    },
    runs: { total: 100, active: 2 },
    agents: { total: 4, active: 1 },
    workflow: { total: 7 },
    ai_usage: ZERO_AI_USAGE,
    charts: {
      execution: { labels: [], success: [], failed: [] },
      ai_tokens: { labels: [], total_tokens: [], cache_tokens: [] },
      deepseek_cost: { labels: [], cost: [] },
    },
    execution_summary: { passed: 0, failed: 0 },
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

  it('挂载时：自动 loadData，数据进入 stats', async () => {
    const result = await mountView()

    expect(fetchDashboardStats).toHaveBeenCalledTimes(1)
    expect(result.stats.value.devices.online).toBe(3)
    expect(result.loading.value).toBe(false)
  })

  it('caseProjectCards：按项目映射名称、计数与工作台路径', async () => {
    const result = await mountView()

    expect(result.caseProjectCards.value).toEqual([
      {
        projectId: 10,
        name: '家电冒烟',
        total: 8,
        color: 'deep',
        path: '/cases/projects/10',
      },
      {
        projectId: 11,
        name: '空项目',
        total: 0,
        color: 'sage',
        path: '/cases/projects/11',
      },
    ])
    expect(result.stats.value.cases.breakdown).toHaveLength(2)
  })

  it('无项目时 caseProjectCards 为空', async () => {
    const raw = makeRaw()
    raw.cases = { total: 0, enabled: 0, breakdown: [] }
    const result = await mountView(raw)

    expect(result.caseProjectCards.value).toEqual([])
  })

  it('getElementItem 命中：返回 typeBreakdown 项', async () => {
    const result = await mountView()

    expect(result.getElementItem('web')).toEqual({ type: 'web', total: 12 })
  })

  it('getElementItem 未命中：回退零值项', async () => {
    const result = await mountView()

    expect(result.getElementItem('api')).toEqual({ type: 'api', total: 0 })
  })

  it('暴露展示配置：页头与 Android 元素分项', async () => {
    const result = await mountView()
    expect(result.PAGE_HEADER.title).toBe('仪表盘')
    expect(result.elementBreakdown).toHaveLength(1)
    expect(result.elementBreakdown.map((e) => e.type)).toEqual(['android'])
  })
})
