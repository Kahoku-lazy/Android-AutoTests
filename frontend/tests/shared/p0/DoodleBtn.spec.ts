/**
 * [P0] DoodleBtn — tone / click / disabled
 */
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DoodleBtn from '@/shared/components/DoodleBtn.vue'

describe('[P0] DoodleBtn', () => {
  it('默认 paper tone 与类名', () => {
    const wrapper = mount(DoodleBtn, { slots: { default: '操作' } })
    expect(wrapper.classes()).toContain('doodle-btn')
    expect(wrapper.classes()).toContain('doodle-btn--paper')
    expect(wrapper.text()).toBe('操作')
  })

  it.each(['danger', 'teal', 'yellow'] as const)('tone=%s 映射类名', (tone) => {
    const wrapper = mount(DoodleBtn, {
      props: { tone },
      slots: { default: tone },
    })
    expect(wrapper.classes()).toContain(`doodle-btn--${tone}`)
  })

  it('点击触发 click', async () => {
    const onClick = vi.fn()
    const wrapper = mount(DoodleBtn, {
      props: { tone: 'teal' },
      attrs: { onClick },
      slots: { default: '校验' },
    })
    await wrapper.trigger('click')
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('disabled 时不可点', async () => {
    const onClick = vi.fn()
    const wrapper = mount(DoodleBtn, {
      props: { tone: 'danger', disabled: true },
      attrs: { onClick },
      slots: { default: '删除' },
    })
    expect(wrapper.attributes('disabled')).toBeDefined()
    expect(wrapper.classes()).toContain('is-disabled')
    await wrapper.trigger('click')
    expect(onClick).not.toHaveBeenCalled()
  })
})
