/**
 * [P0] AppCard — 钉板壳 / tone·tilt / pin / 旧 color 回退
 * el-card 用透传 stub：VTU 默认 stub 会吞掉内部图钉节点，改断言 --pin class + CSS 变量。
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, defineComponent } from 'vue'
import AppCard from '@/shared/components/AppCard.vue'

const ElCardStub = defineComponent({
  name: 'ElCard',
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () =>
      h(
        'div',
        { class: ['el-card', attrs.class], style: attrs.style as string | undefined },
        slots.default?.(),
      )
  },
})

function mountCard(props: Record<string, unknown> = {}, slot = '内容') {
  return mount(AppCard, {
    props,
    slots: { default: slot },
    global: { stubs: { 'el-card': ElCardStub, ElCard: ElCardStub } },
  })
}

describe('[P0] AppCard', () => {
  it('默认渲染 ac-card、图钉 class 与默认 tilt', () => {
    const wrapper = mountCard()
    expect(wrapper.classes()).toContain('ac-card')
    expect(wrapper.classes()).toContain('ac-card--pin')
    expect(wrapper.attributes('style')).toContain('--ac-tilt: 0.3deg')
    expect(wrapper.text()).toContain('内容')
  })

  it('tone 写入 --ac-accent；pin=false 去掉图钉 class', () => {
    const wrapper = mountCard({ tone: 'var(--c-case)', tilt: -1.2, pin: false })
    const style = wrapper.attributes('style') ?? ''
    expect(style).toContain('--ac-accent: var(--c-case)')
    expect(style).toContain('--ac-tilt: -1.2deg')
    expect(wrapper.classes()).not.toContain('ac-card--pin')
  })

  it('无 tone 时旧 color 映射到模块令牌', () => {
    const wrapper = mountCard({ color: 'app-device' })
    expect(wrapper.attributes('style')).toContain('--ac-accent: var(--c-device)')
  })
})
