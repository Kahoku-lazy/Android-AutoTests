/**
 * [P0] 线路卡身份区（头像 + 两行）+ 底栏配置按键；校验与连通状态已下线
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentRouteCard from '@/modules/ai-assistant/components/AgentRouteCard.vue'

const stubs = {
  DoodleNote: {
    template:
      '<article class="doodle-note">'
      + '<header><slot name="header" /></header>'
      + '<div class="body"><slot /></div>'
      + '<footer><slot name="actions" /></footer>'
      + '</article>',
  },
  DoodleBtn: {
    template: '<button type="button"><slot /></button>',
  },
}

function mountCard(props: Record<string, unknown> = {}) {
  return mount(AgentRouteCard, {
    props: {
      agentName: '测试助手',
      ...props,
    },
    global: { stubs },
  })
}

describe('AgentRouteCard 身份区', () => {
  it('左头像 + 右两行：名称 / 职责：UI自动化；无独立「控制设备」标题', () => {
    const w = mountCard()
    expect(w.find('.route-avatar').exists()).toBe(true)
    expect(w.find('.route-agent-name').text()).toBe('测试助手')
    expect(w.find('.route-duty').text()).toBe('职责：UI自动化')
    expect(w.text()).not.toContain('控制设备')
    expect(w.find('.route-func-title').exists()).toBe(false)
  })

  it('不展示连通状态徽标', () => {
    const w = mountCard()
    expect(w.find('.route-conn-badge').exists()).toBe(false)
    expect(w.text()).not.toContain('已连通')
    expect(w.text()).not.toContain('校验中')
  })

  it('canManage 时底栏只有配置', () => {
    const w = mountCard({ canManage: true })
    const buttons = w.findAll('button')
    expect(buttons.map((b) => b.text())).toEqual(['配置'])
  })

  it('canManage=false 时无配置按键', () => {
    const w = mountCard({ canManage: false })
    expect(w.findAll('button')).toHaveLength(0)
    expect(w.find('.route-agent-name').exists()).toBe(true)
    expect(w.find('.route-duty').exists()).toBe(true)
  })
})
