/**
 * [P0] 必测 — 串口日志页（spec: serial-log-page）
 *
 * 断言：① 默认选中无线端口，且页面标题为「串口日志」；
 * ② 切到日志关键词后只渲染关键词面板；③ 权限随 is_superuser 传入端口面板；
 * ④ 切 Tab 不触发任何 toggle 写请求。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const authState = vi.hoisted(() => ({ isSuperuser: true }))

vi.mock('@/shared/composables/useAuthUser', async () => {
  const { ref } = await import('vue')
  return {
    useAuthUser: () => ({ isSuperuser: ref(authState.isSuperuser), loaded: ref(true) }),
  }
})

const api = vi.hoisted(() => ({
  fetchLogPorts: vi.fn().mockResolvedValue({ status: true, data: { ports: [] } }),
  fetchLogKeywords: vi.fn().mockResolvedValue({ status: true, data: { keywords: [] } }),
  fetchLogPortLines: vi.fn(),
  toggleLogPort: vi.fn(),
}))

vi.mock('@/modules/serial-log/api', () => api)

import SerialLogPage from '@/modules/serial-log/index.vue'

const AppTabsStub = {
  props: ['items', 'modelValue'],
  emits: ['update:modelValue'],
  template: `
    <div class="stub-tabs">
      <button
        v-for="it in items"
        :key="it.key"
        class="stub-tab"
        @click="$emit('update:modelValue', it.key)"
      >{{ it.label }}</button>
      <slot name="ports" />
      <slot name="keywords" />
    </div>
  `,
}

const stubs = {
  WorkbenchHeader: {
    props: ['title', 'subtitle', 'icon'],
    template: '<header class="stub-header">{{ title }}</header>',
  },
  AppTabs: AppTabsStub,
  WifiPortPanel: {
    props: ['canManage'],
    template: '<div class="stub-ports" :data-can-manage="String(canManage)" />',
  },
  LogKeywordPanel: { template: '<div class="stub-keywords" />' },
}

function mountPage() {
  return mount(SerialLogPage, { global: { stubs } })
}

describe('[P0] SerialLogPage', () => {
  beforeEach(() => {
    authState.isSuperuser = true
    api.toggleLogPort.mockClear()
  })

  it('页头标题为「串口日志」，默认渲染无线端口', () => {
    const w = mountPage()
    expect(w.find('.stub-header').text()).toBe('串口日志')
    expect(w.find('.stub-ports').exists()).toBe(true)
    expect(w.find('.stub-keywords').exists()).toBe(false)
  })

  it('只有两个 Tab，切到日志关键词后只渲染关键词面板', async () => {
    const w = mountPage()
    const tabs = w.findAll('.stub-tab')
    expect(tabs.map((t) => t.text())).toEqual(['无线端口', '日志关键词'])
    await tabs[1].trigger('click')
    expect(w.find('.stub-keywords').exists()).toBe(true)
    expect(w.find('.stub-ports').exists()).toBe(false)
  })

  it('超级管理员可操作开关（canManage=true）', () => {
    const w = mountPage()
    expect(w.find('.stub-ports').attributes('data-can-manage')).toBe('true')
  })

  it('普通用户传入只读（canManage=false）', () => {
    authState.isSuperuser = false
    const w = mountPage()
    expect(w.find('.stub-ports').attributes('data-can-manage')).toBe('false')
  })

  it('切换 Tab 不触发写请求', async () => {
    const w = mountPage()
    await w.findAll('.stub-tab')[1].trigger('click')
    await w.findAll('.stub-tab')[0].trigger('click')
    expect(api.toggleLogPort).not.toHaveBeenCalled()
  })
})
