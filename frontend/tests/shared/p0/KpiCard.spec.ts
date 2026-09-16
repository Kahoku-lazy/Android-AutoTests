/**
 * [P0] KpiCard — doodle 壳 / 双变体 / 点击与键盘
 */
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import KpiCard from '@/shared/components/KpiCard.vue'

describe('[P0] KpiCard', () => {
  it('kpi 默认：渲染 doodle 壳类名与 label/value', () => {
    const wrapper = mount(KpiCard, {
      props: { label: '通过率', value: '96%', color: 'var(--c-dashboard)', shape: 'circle' },
    })
    expect(wrapper.classes()).toContain('kpi-card')
    expect(wrapper.classes()).toContain('kpi-card--kpi')
    expect(wrapper.find('.kpi-card__label').text()).toBe('通过率')
    expect(wrapper.find('.kpi-card__value').text()).toBe('96%')
    expect(wrapper.find('.kpi-card__shape--circle').exists()).toBe(true)
  })

  it('kpi：点击触发 click', async () => {
    const onClick = vi.fn()
    const wrapper = mount(KpiCard, {
      props: { label: '失败', value: 9 },
      attrs: { onClick },
    })
    await wrapper.trigger('click')
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('entry：展示标题/描述/进入，装饰不抢交互', async () => {
    const onClick = vi.fn()
    const wrapper = mount(KpiCard, {
      props: {
        variant: 'entry',
        label: '工作流',
        value: 5,
        desc: '核心指标实时更新',
        deco: 'tape',
        live: true,
        color: 'var(--c-workflow)',
      },
      attrs: { onClick },
    })
    expect(wrapper.classes()).toContain('kpi-card--entry')
    expect(wrapper.find('.kpi-card__title').text()).toBe('工作流')
    expect(wrapper.find('.kpi-card__desc').text()).toBe('核心指标实时更新')
    expect(wrapper.find('.kpi-card__enter').exists()).toBe(true)
    expect(wrapper.find('.kpi-card__tape').exists()).toBe(true)
    expect(wrapper.find('.kpi-card__live').exists()).toBe(true)

    await wrapper.find('.kpi-card__enter').trigger('click')
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('entry：键盘 Enter 激活', async () => {
    const onClick = vi.fn()
    const wrapper = mount(KpiCard, {
      props: { variant: 'entry', label: '设备', value: 12 },
      attrs: { onClick },
    })
    await wrapper.trigger('keydown', { key: 'Enter' })
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('entry：clickable=false 时不可点且无进入按钮', async () => {
    const onClick = vi.fn()
    const wrapper = mount(KpiCard, {
      props: { variant: 'entry', label: '只读', value: 1, clickable: false },
      attrs: { onClick },
    })
    expect(wrapper.attributes('role')).toBeUndefined()
    expect(wrapper.find('.kpi-card__enter').exists()).toBe(false)
    await wrapper.trigger('click')
    expect(onClick).not.toHaveBeenCalled()
  })
})
