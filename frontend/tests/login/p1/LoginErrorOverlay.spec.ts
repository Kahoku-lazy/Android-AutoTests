/**
 * [P1] 建议测 — 登录错误浮层（展示 / 关闭 / ESC / 点遮罩）
 * 实现已收敛为 el-dialog 薄封装（L5 覆盖层统一走 EP），断言随职责迁移到 EP DOM。
 * 目录：tests/login/p1/
 *
 * stub 口径：不注册真实 Element Plus（vite.config.js「单测用 stub 替换 el-*」），
 * 由本 spec 自带内联 stub（与 LoginCard.spec.ts / AccountSwitchPrompt.spec.ts 一致），
 * 模型化组件真正依赖的 EP 契约：.el-overlay（遮罩）> .el-dialog、
 * 默认插槽 + footer 具名插槽、ESC 与点遮罩均关闭。
 * 缺少 el-dialog stub 时既不产生这两个类名，footer 具名插槽也不渲染。
 */
import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginErrorOverlay from '@/views/components/LoginErrorOverlay.vue'

const stubs = {
  'el-dialog': {
    name: 'ElDialogStub',
    // 必须用**带类型**的对象写法：模板里 `append-to-body` 是无值属性，
    // 只有 Boolean 类型的 prop 才会被 Vue 把空字符串强转成 true（数组写法会拿到 ''）
    props: { modelValue: Boolean, title: String, width: String, appendToBody: Boolean },
    emits: ['update:modelValue'],
    // 遮罩点击关闭 = EP 默认行为；组件未设 close-on-click-modal="false"，
    // 因为它承载的是纯展示的错误提示（见 frontend-l5-overlay「Read-only overlay stays dismissible」）
    template: `
      <div v-if="modelValue" class="el-overlay" @click="close">
        <div
          class="el-dialog"
          :data-append-to-body="appendToBody ? 'true' : 'false'"
          @click.stop
          @keydown.esc="close"
        >
          <header class="el-dialog__header"><span class="el-dialog__title">{{ title }}</span></header>
          <div class="el-dialog__body"><slot /></div>
          <footer class="el-dialog__footer"><slot name="footer" /></footer>
        </div>
      </div>`,
    methods: {
      close() {
        this.$emit('update:modelValue', false)
      },
    },
  },
  // 不在 stub 里再 $emit('click')：父级 @click 会随属性透传到这个 button，
  // 再 emit 一次就会叠成两次（同 AccountSwitchPrompt.spec.ts 的既有注释）
  'el-button': {
    template: '<button type="button" class="el-button"><slot /></button>',
  },
}

function mountOverlay(props: { visible: boolean; message: string }) {
  return mount(LoginErrorOverlay, {
    props,
    attachTo: document.body,
    global: {
      // Teleport 留在组件树内，便于 find
      stubs: { ...stubs, teleport: true, transition: false },
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

  it('遮罩跳出 transform 包含块：el-dialog 收到 append-to-body', () => {
    const wrapper = mountOverlay({ visible: true, message: '失败' })
    // 守卫 frontend-l5-overlay「Blocking overlays escape transformed ancestors」：
    // 挂载点 .meeting-doodle 带 transform: rotate(1.2deg)，不 Teleport 到 body
    // 遮罩就只盖住那张便签卡（真实尺寸证据见 temps/login-layer-map 的实测复验）。
    // 断言走 stub 透出的 data-*：未收到 append-to-body 时为 'false'。
    expect(wrapper.find('.el-dialog').attributes('data-append-to-body')).toBe('true')
  })
})
