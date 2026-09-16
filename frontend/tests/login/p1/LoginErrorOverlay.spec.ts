/**
 * [P1] 建议测 — 登录错误浮层（展示 / 关闭 / ESC / 点遮罩）
 * 实现已收敛为 el-dialog 薄封装（L5 覆盖层统一走 EP），断言随职责迁移到 EP DOM。
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
      // Teleport 留在组件树内，便于 find
      stubs: { teleport: true, transition: false },
    },
  })
}

describe('[P1] LoginErrorOverlay', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('visible=false 时：不渲染内容', () => {
    const wrapper = mountOverlay({ visible: false, message: '失败' })
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('visible=true 时：展示错误文案', () => {
    const wrapper = mountOverlay({ visible: true, message: '密码错误' })
    expect(wrapper.text()).toContain('密码错误')
  })

  it('点「知道了」：触发 close', async () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    await wrapper.find('[data-testid="login-error-dismiss"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('visible=false 时：ESC 不触发 close', () => {
    const wrapper = mountOverlay({ visible: false, message: '失败' })
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('按 ESC：触发 close', async () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    await wrapper.find('.el-dialog').trigger('keydown.esc')
    expect((wrapper.emitted('close') ?? []).length).toBeGreaterThan(0)
  })

  it('点击遮罩：触发 close', async () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    await wrapper.find('.el-overlay').trigger('click')
    expect((wrapper.emitted('close') ?? []).length).toBeGreaterThan(0)
  })
})
