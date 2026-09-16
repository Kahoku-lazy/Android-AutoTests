/**
 * [P0] SketchCard — 撕纸壳 / 空描述 / 删除不冒泡 / 键盘进入
 */
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SketchCard from '@/shared/components/SketchCard.vue'
import { sketchTiltAt, sketchToneAt } from '@/shared/helpers/sketchCard'

describe('[P0] SketchCard', () => {
  it('cycle：index 0 与 1 的 tone 不同，index 8 回到 0', () => {
    expect(sketchToneAt(0)).toBe('var(--c-dashboard)')
    expect(sketchToneAt(1)).toBe('var(--c-device)')
    expect(sketchToneAt(8)).toBe(sketchToneAt(0))
    expect(sketchTiltAt(0)).toBe(-1.5)
  })

  it('渲染撕纸壳、标题与空描述占位', () => {
    const wrapper = mount(SketchCard, {
      props: { title: '制冰机回归', tone: 'var(--c-case)', meta: '24 条 · 09-12' },
    })
    expect(wrapper.classes()).toContain('sketch-card')
    expect(wrapper.find('.sketch-card__title').text()).toBe('制冰机回归')
    expect(wrapper.find('.sketch-card__desc.is-muted').text()).toBe('暂无描述')
    expect(wrapper.find('.sketch-card__pg').text()).toBe('24 条 · 09-12')
    expect(wrapper.find('.sketch-card__kill').exists()).toBe(false)
  })

  it('点击卡片触发 activate；删除不冒泡', async () => {
    const onActivate = vi.fn()
    const onDelete = vi.fn()
    const wrapper = mount(SketchCard, {
      props: { title: '可删', deletable: true },
      attrs: { onActivate, onDelete },
    })
    await wrapper.find('.sketch-card__kill').trigger('click')
    expect(onDelete).toHaveBeenCalledTimes(1)
    expect(onActivate).not.toHaveBeenCalled()
    await wrapper.trigger('click')
    expect(onActivate).toHaveBeenCalledTimes(1)
  })

  it('键盘 Enter 激活进入', async () => {
    const onActivate = vi.fn()
    const wrapper = mount(SketchCard, {
      props: { title: '键盘' },
      attrs: { onActivate },
    })
    await wrapper.trigger('keydown', { key: 'Enter' })
    expect(onActivate).toHaveBeenCalledTimes(1)
  })
})
