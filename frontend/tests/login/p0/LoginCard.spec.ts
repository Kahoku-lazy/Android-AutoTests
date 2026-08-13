/**
 * [P0] 必测 — 登录卡片交互（提交/禁用/记住账号/去注册）
 * 目录：tests/login/p0/
 */
/**
 * [P0] 必测 — 登录卡主交互（提交 / 禁用 / 记住账号 / 去注册）
 * 目录：tests/login/p0/
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginCard from '@/views/components/LoginCard.vue'

const stubs = {
  AppCard: { template: '<div class="app-card"><slot /></div>' },
  IconUser: true,
  IconLock: true,
  'el-input': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template:
      '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
  'el-button': {
    props: ['disabled', 'loading'],
    template: '<button class="el-button" :disabled="disabled"><slot /></button>',
  },
  'el-switch': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template:
      '<input type="checkbox" class="el-switch" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
  },
}

function mountCard(props: Record<string, unknown> = {}) {
  return mount(LoginCard, {
    props: {
      username: 'alice',
      password: 'secret',
      errors: {},
      canSubmit: true,
      ...props,
    },
    global: { stubs },
  })
}

describe('[P0] LoginCard', () => {
  it('展示字段错误文案', () => {
    const wrapper = mountCard({
      errors: { username: '请输入用户名', password: '请输入密码' },
      canSubmit: false,
    })
    expect(wrapper.text()).toContain('请输入用户名')
    expect(wrapper.text()).toContain('请输入密码')
  })

  it('canSubmit=false 时：登录按钮禁用', () => {
    const wrapper = mountCard({ canSubmit: false })
    expect(wrapper.find('button.el-button').attributes('disabled')).toBeDefined()
  })

  it('点击登录：触发 submit', async () => {
    const wrapper = mountCard()
    await wrapper.find('button.el-button').trigger('click')
    expect(wrapper.emitted('submit')).toHaveLength(1)
  })

  it('点击去注册：触发 switchToRegister', async () => {
    const wrapper = mountCard()
    await wrapper.find('.form-toggle').trigger('click')
    expect(wrapper.emitted('switchToRegister')).toHaveLength(1)
  })

  it('勾选记住账号：触发 update:rememberMe', async () => {
    const wrapper = mountCard({ rememberMe: false })
    await wrapper.find('input.el-switch').setValue(true)
    expect(wrapper.emitted('update:rememberMe')?.[0]).toEqual([true])
  })
})
