/**
 * [P0] 线路卡身份区（头像+三行）+ 连通三态 + 底栏按键
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
  it('左头像 + 右三行：名称 / 职责：UI自动化 / 状态；无独立「控制设备」标题', () => {
    const w = mountCard({ routeStatus: 'ready' })
    expect(w.find('.route-avatar').exists()).toBe(true)
    expect(w.find('.route-agent-name').text()).toBe('测试助手')
    expect(w.find('.route-duty').text()).toBe('职责：UI自动化')
    expect(w.find('.route-conn-badge').text()).toBe('已连通，可执行任务')
    expect(w.text()).not.toContain('控制设备')
    expect(w.find('.route-func-title').exists()).toBe(false)
  })

  it('canManage 时底栏有校验与配置', () => {
    const w = mountCard({ canManage: true, routeStatus: 'ready' })
    const buttons = w.findAll('button')
    expect(buttons.map((b) => b.text())).toEqual(['校验', '配置'])
  })

  it('canManage=false 时无校验/配置按键', () => {
    const w = mountCard({ canManage: false, routeStatus: 'ready' })
    expect(w.findAll('button')).toHaveLength(0)
    expect(w.find('.route-agent-name').exists()).toBe(true)
    expect(w.find('.route-duty').exists()).toBe(true)
  })
})

describe('AgentRouteCard 连通三态', () => {
  it('ready → 已连通，可执行任务', () => {
    const w = mountCard({ routeStatus: 'ready' })
    expect(w.find('.route-conn-badge').text()).toBe('已连通，可执行任务')
    expect(w.find('.route-conn-badge').classes()).toContain('is-ready')
  })

  it('unusable → 秘钥已连接，但无法使用', () => {
    const w = mountCard({ routeStatus: 'unusable' })
    expect(w.find('.route-conn-badge').text()).toBe('秘钥已连接，但无法使用')
    expect(w.find('.route-conn-badge').classes()).toContain('is-unusable')
  })

  it('offline → 连接失败，小助手断线', () => {
    const w = mountCard({ routeStatus: 'offline' })
    expect(w.find('.route-conn-badge').text()).toBe('连接失败，小助手断线')
    expect(w.find('.route-conn-badge').classes()).toContain('is-offline')
  })

  it('探测中显示校验中…，不是未检测', () => {
    const w = mountCard({ testing: true })
    expect(w.find('.route-conn-badge').text()).toBe('校验中…')
    expect(w.text()).not.toContain('未检测')
  })

  it('无 status 且非 testing 时显示校验中…（进页等待）', () => {
    const w = mountCard({})
    expect(w.find('.route-conn-badge').text()).toBe('校验中…')
  })
})
