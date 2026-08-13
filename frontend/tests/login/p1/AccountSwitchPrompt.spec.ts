/**
 * [P1] 建议测 — 账号切换提示卡（展示 + emit）
 * 目录：tests/login/p1/
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AccountSwitchPrompt from '@/views/components/AccountSwitchPrompt.vue'

const stubs = {
  AppCard: { template: '<div class="app-card"><slot /></div>' },
  IconUser: true,
  IconPlus: true,
  // 不要在 stub 里再 $emit('click')，否则会与父级 @click 叠成两次
  'el-button': {
    template: '<button type="button" class="el-button"><slot /></button>',
  },
}

describe('[P1] AccountSwitchPrompt', () => {
  it('展示已登录用户名', () => {
    const wrapper = mount(AccountSwitchPrompt, {
      props: { existingUsername: 'alice' },
      global: { stubs },
    })
    expect(wrapper.text()).toContain('alice')
    expect(wrapper.text()).toContain('检测到已登录账号')
  })

  it('点击切换账号：触发 switchTo', async () => {
    const wrapper = mount(AccountSwitchPrompt, {
      props: { existingUsername: 'alice' },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-button')
    await buttons[0].trigger('click')
    expect(wrapper.emitted('switchTo')).toHaveLength(1)
  })

  it('点击添加新账号：触发 addNew', async () => {
    const wrapper = mount(AccountSwitchPrompt, {
      props: { existingUsername: 'alice' },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-button')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('addNew')).toHaveLength(1)
  })
})
