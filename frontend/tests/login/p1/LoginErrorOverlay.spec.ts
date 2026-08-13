/**
 * [P1] 建议测 — 登录错误浮层（展示 / 关闭 / ESC / 点遮罩）
 * 目录：tests/login/p1/
 */
import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginErrorOverlay from '@/views/components/LoginErrorOverlay.vue'

function mountOverlay(props: { visible: boolean; message: string }) {
  return mount(LoginErrorOverlay, {
    props,
    attachTo: document.body,
    global: {
      // Teleport/Transition 留在组件树内，便于 find + emitted
      stubs: { teleport: true, transition: false },
    },
  })
}

describe('[P1] LoginErrorOverlay', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('visible=false 时不渲染内容', () => {
    const wrapper = mountOverlay({ visible: false, message: '失败' })
    expect(wrapper.find('.error-overlay').exists()).toBe(false)
  })

  it('visible=true 时展示错误文案', () => {
    const wrapper = mountOverlay({ visible: true, message: '密码错误' })
    expect(wrapper.text()).toContain('密码错误')
  })

  it('点「知道了」触发 close', async () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    await wrapper.find('.error-card__btn').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('按 ESC 触发 close', () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('visible=false 时 ESC 不触发 close', () => {
    const wrapper = mountOverlay({ visible: false, message: '失败' })
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('点击遮罩（self）触发 close', async () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    await wrapper.find('.error-overlay').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})
