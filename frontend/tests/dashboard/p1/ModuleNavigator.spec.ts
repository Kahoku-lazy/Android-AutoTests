/**
 * [P1] 建议测 — 模块导航卡（8 大模块渲染 / 统计数值注入 / 点击跳转）
 * 目录：tests/dashboard/p1/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ModuleNavigator from '@/modules/dashboard/components/ModuleNavigator.vue'
import { staggerReveal } from '@/shared/animations'
import type { DashboardStats } from '@/shared/types/dashboard'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

vi.mock('@/shared/animations', () => ({
  staggerReveal: vi.fn(),
}))

function makeStats(): DashboardStats {
  return {
    devices: { online: 3, total: 5, trend: 0 },
    cases: { total: 20, enabled: 18, trend: 0, breakdown: [] },
    elements: { total: 42, pages: 6, breakdown: [], typeBreakdown: [] },
    runs: { total: 100, active: 2, trend: 0 },
    agents: { total: 4, active: 1, trend: 0 },
    reports: { total: 9 },
    workflow: { total: 7, page_flows: 3, test_cases: 4 },
  }
}

function mountNav(stats: DashboardStats = makeStats()) {
  return mount(ModuleNavigator, { props: { stats } })
}

describe('[P1] ModuleNavigator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染 9 张模块卡片（8 模块 + 仪表盘快捷入口）', () => {
    const wrapper = mountNav()
    expect(wrapper.findAll('.module-card')).toHaveLength(9)
  })

  it('stat 数值注入卡片：在线设备 / 元素数 / 运行中', () => {
    const wrapper = mountNav()
    const cards = wrapper.findAll('.module-card')

    const deviceCard = cards.find((c) => c.text().includes('设备管理'))!
    expect(deviceCard.find('.module-stat strong').text()).toBe('3')
    expect(deviceCard.text()).toContain('在线设备')

    const elementCard = cards.find((c) => c.text().includes('元素定位'))!
    expect(elementCard.find('.module-stat strong').text()).toBe('42')

    const runnerCard = cards.find((c) => c.text().includes('执行引擎'))!
    expect(runnerCard.find('.module-stat strong').text()).toBe('2')
  })

  it('数值为 0 仍显示 0；无数值模块只显示标签', () => {
    const wrapper = mountNav({ ...makeStats(), devices: { online: 0, total: 0, trend: 0 } })
    const cards = wrapper.findAll('.module-card')

    const deviceCard = cards.find((c) => c.text().includes('设备管理'))!
    expect(deviceCard.find('.module-stat strong').text()).toBe('0')

    const inspectorCard = cards.find((c) => c.text().includes('设备检查器'))!
    expect(inspectorCard.find('.module-stat strong').exists()).toBe(false)
    expect(inspectorCard.text()).toContain('设备检查器')
  })

  it('点击卡片跳转对应模块路由', async () => {
    const wrapper = mountNav()
    const cards = wrapper.findAll('.module-card')

    await cards.find((c) => c.text().includes('AI 助手'))!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/ai-assistant')
  })

  it('键盘 Enter 触发跳转', async () => {
    const wrapper = mountNav()
    const cards = wrapper.findAll('.module-card')

    await cards.find((c) => c.text().includes('工作流工作台'))!.trigger('keydown', { key: 'Enter' })

    expect(pushMock).toHaveBeenCalledWith('/workflow')
  })

  it('挂载时触发入场动画', async () => {
    mountNav()
    await flushPromises()
    expect(staggerReveal).toHaveBeenCalled()
  })
})
