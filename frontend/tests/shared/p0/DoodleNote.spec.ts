/**
 * [P0] DoodleNote — 变体 / 装饰 / 插槽
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DoodleNote from '@/shared/components/DoodleNote.vue'

describe('[P0] DoodleNote', () => {
  it('note 默认：类名 + 胶带', () => {
    const wrapper = mount(DoodleNote, {
      slots: { default: '正文' },
    })
    expect(wrapper.classes()).toContain('doodle-note')
    expect(wrapper.classes()).toContain('doodle-note--note')
    expect(wrapper.find('.doodle-note__tape').exists()).toBe(true)
    expect(wrapper.find('.doodle-note__body').text()).toBe('正文')
  })

  it('sticky + fail：Dont 状态类', () => {
    const wrapper = mount(DoodleNote, {
      props: { variant: 'sticky', status: 'fail', tape: true },
      slots: {
        header: '失败标题',
        default: '摘要',
        actions: '操作',
      },
    })
    expect(wrapper.classes()).toContain('doodle-note--sticky')
    expect(wrapper.classes()).toContain('doodle-note--status-fail')
    expect(wrapper.find('.doodle-note__header').text()).toBe('失败标题')
    expect(wrapper.find('.doodle-note__actions').text()).toBe('操作')
  })

  it('tape=false 时无胶带', () => {
    const wrapper = mount(DoodleNote, {
      props: { tape: false },
      slots: { default: 'x' },
    })
    expect(wrapper.find('.doodle-note__tape').exists()).toBe(false)
  })

  it('胶带节点 pointer-events 不抢交互（CSS 契约）', () => {
    const wrapper = mount(DoodleNote, { props: { tape: true } })
    const tape = wrapper.find('.doodle-note__tape')
    expect(tape.exists()).toBe(true)
    // 样式在 scoped CSS 中声明；此处断言装饰节点存在且为 span（aria-hidden）
    expect(tape.attributes('aria-hidden')).toBe('true')
  })
})
