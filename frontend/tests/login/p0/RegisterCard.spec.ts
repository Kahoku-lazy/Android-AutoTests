/**
 * [P0] 必测 — 注册卡片交互（提交/禁用/去登录）
 * 目录：tests/login/p0/
 */
/**
 * [P0] 必测 — 注册卡主交互（提交 / 禁用 / 去登录）
 * 目录：tests/login/p0/
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import RegisterCard from '@/views/components/RegisterCard.vue'

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
}

function mountCard(props: Record<string, unknown> = {}) {
  return mount(RegisterCard, {
    props: {
      username: 'bob',
      email: 'bob@example.com',
      password: '123456',
      password2: '123456',
      errors: {},
      canSubmit: true,
      ...props,
    },
    global: { stubs },
  })
}

describe('[P0] RegisterCard', () => {
  it('展示校验错误', () => {
    const wrapper = mountCard({
      errors: { password2: '两次密码不一致' },
      canSubmit: false,
    })
    expect(wrapper.text()).toContain('两次密码不一致')
  })

  it('canSubmit=false 时：注册按钮禁用', () => {
    const wrapper = mountCard({ canSubmit: false })
    expect(wrapper.find('button.el-button').attributes('disabled')).toBeDefined()
  })

  it('点击完成注册：触发 submit', async () => {
    const wrapper = mountCard()
    await wrapper.find('button.el-button').trigger('click')
    expect(wrapper.emitted('submit')).toHaveLength(1)
  })

  it('点击去登录：触发 switchToLogin', async () => {
    const wrapper = mountCard()
    await wrapper.find('.form-toggle').trigger('click')
    expect(wrapper.emitted('switchToLogin')).toHaveLength(1)
  })
})
