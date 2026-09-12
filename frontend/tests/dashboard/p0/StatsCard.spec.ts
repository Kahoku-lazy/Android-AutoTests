/**
 * [P0] 必测 — 仪表盘统计卡主交互（数值展示 / 趋势文案 / loading 骨架 / 点击跳转）
 * 目录：tests/dashboard/p0/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import StatsCard from '@/modules/dashboard/components/StatsCard.vue'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

function mountCard(props: Record<string, unknown> = {}) {
  return mount(StatsCard, {
    props,
    global: { stubs: { 'el-button': true } },
  })
}

describe('[P0] StatsCard', () => {
  beforeEach(() => {
    pushMock.mockClear()
  })

  it('展示：label 与千分位数值', () => {
    const wrapper = mountCard({ label: '在线设备', value: 1234 })
    expect(wrapper.text()).toContain('在线设备')
    expect(wrapper.find('.stats-card__stat strong').text()).toBe('1,234')
  })

  it('prefix / suffix：拼接在数值两侧', () => {
    const wrapper = mountCard({ value: 1234, prefix: '¥', suffix: ' 台' })
    expect(wrapper.find('.stats-card__stat strong').text()).toBe('¥1,234 台')
  })

  it('趋势为正：显示 ↑x% 文案', () => {
    const wrapper = mountCard({ value: 10, trend: 5, trendLabel: '活跃' })
    expect(wrapper.text()).toContain('↑5% 活跃')
  })

  it('趋势为负：显示 ↓x% 文案（取绝对值）', () => {
    const wrapper = mountCard({ value: 10, trend: -3, trendLabel: '活跃' })
    expect(wrapper.text()).toContain('↓3% 活跃')
  })

  it('趋势为 0：只显示 trendLabel，无箭头', () => {
    const wrapper = mountCard({ value: 10, trend: 0, trendLabel: '活跃' })
    expect(wrapper.find('.stats-card__stat small').text()).toBe('活跃')
  })

  it('desc 缺省时：显示默认描述', () => {
    const wrapper = mountCard({})
    expect(wrapper.find('.stats-card__desc').text()).toBe('核心指标实时更新')
  })

  it('loading=true：显示骨架屏，不显示数值', () => {
    const wrapper = mountCard({ value: 42, loading: true })
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
    expect(wrapper.find('.stats-card__stat').exists()).toBe(false)
  })

  it('有 path：卡片可点，点击跳转目标路由', async () => {
    const wrapper = mountCard({ value: 3, path: '/devices' })
    expect(wrapper.attributes('role')).toBe('button')

    await wrapper.trigger('click')

    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith('/devices')
  })

  it('点击「进入」按钮：同样跳转且不重复触发', async () => {
    const wrapper = mountCard({ value: 3, path: '/devices' })

    await wrapper.find('.stats-card__enter').trigger('click')

    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith('/devices')
  })

  it('无 path：不可点、无进入按钮，点击不跳转', async () => {
    const wrapper = mountCard({ value: 3 })
    expect(wrapper.attributes('role')).toBeUndefined()
    expect(wrapper.find('.stats-card__enter').exists()).toBe(false)

    await wrapper.trigger('click')

    expect(pushMock).not.toHaveBeenCalled()
  })

  it('键盘 Enter：触发跳转', async () => {
    const wrapper = mountCard({ value: 3, path: '/reports' })

    await wrapper.trigger('keydown', { key: 'Enter' })

    expect(pushMock).toHaveBeenCalledWith('/reports')
  })
})
