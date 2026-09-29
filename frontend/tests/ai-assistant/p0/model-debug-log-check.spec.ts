/**
 * [P0] 必测 — 调试台的日志检查块（spec: ai-model-debug）
 *
 * 目录：tests/ai-assistant/p0/
 * 断言：① 对话返回带该块 → 页面在助手消息内渲染时间点 / 截图路径 / 命中关键词（含 composable 透传）；
 * ② 无日志证据 → 只有时间点与截图；③ 无该键 → 不渲染该块；
 * ④ 服务端说未截图时如实呈现；⑤ 块内只读。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

vi.mock('vue-router', async () => {
  const { reactive } = await import('vue')
  return {
    useRoute: () => ({ params: reactive({ role: 'executor' }) }),
    useRouter: () => ({ push: vi.fn() }),
  }
})

const fetchConfig = vi.fn()
const chat = vi.fn()
const listDevices = vi.fn()

vi.mock('@/modules/ai-assistant/api/toolbox', () => ({
  fetchModelDebugConfig: (...args: unknown[]) => fetchConfig(...args),
  chatWithModelDebug: (...args: unknown[]) => chat(...args),
}))

vi.mock('@/modules/ai-assistant/api/tasks', () => ({
  listDevices: (...args: unknown[]) => listDevices(...args),
}))

import ModelDebugPage from '@/modules/ai-assistant/ModelDebugPage.vue'

const CLICK_TIME = '2026-09-28 10:51:03.219'
const SHOT = 'ai_tasks/debug/s1.jpg'

const LOG = {
  conclusion: 'hit',
  window_line_count: 2,
  hits: [{ keyword: 'switch_off', grade: 'strong', count: 1 }],
}

const CONFIG = {
  agent_id: 1,
  agent_name: '调试智能体',
  role: {
    role: 'executor',
    label: '执行模型',
    vision: true,
    needs_device: true,
    model: {
      provider: 'deepseek',
      model_name: 'stub-model',
      has_api_key: true,
      configured: true,
    },
    prompt: 'P',
    tools: [],
  },
  skills: { gate_on: false, shared_by_roles: true, items: [] },
}

const stubs = {
  'el-collapse': { template: '<div class="el-collapse"><slot /></div>' },
  'el-collapse-item': {
    props: ['title', 'name'],
    template: '<div class="el-collapse-item"><span>{{ title }}</span><slot /></div>',
  },
  'el-select': { template: '<div class="el-select"><slot /></div>' },
  'el-option': { template: '<div class="el-option" />' },
  'el-image': { props: ['src'], template: '<img class="el-image" :src="src" v-bind="$attrs" />' },
  WorkbenchHeader: { template: '<div class="wb-header" />' },
  WorkbenchCrumbs: { template: '<div class="wb-crumbs" />' },
}

async function mountPage() {
  fetchConfig.mockResolvedValue({ status: true, data: CONFIG })
  listDevices.mockResolvedValue({ status: true, data: { devices: [] } })
  const wrapper = mount(ModelDebugPage, { global: { stubs } })
  await nextTick()
  await nextTick()
  return wrapper
}

/** 直接把助手消息塞进页面状态：本用例只验证渲染口径 */
async function pushAssistant(wrapper: Awaited<ReturnType<typeof mountPage>>, logCheck?: unknown) {
  const vm = wrapper.vm as unknown as { messages: unknown[] }
  vm.messages.push({
    id: 2,
    role: 'assistant',
    content: '已点击开关',
    model_name: 'stub-model',
    tool_usage: [{ type: 'result', name: 'xpath_action', output: '{"clicked": true}' }],
    log_check: logCheck,
  })
  await nextTick()
}

describe('[P0] 调试台日志检查块', () => {
  beforeEach(() => {
    fetchConfig.mockReset()
    chat.mockReset()
    listDevices.mockReset()
  })

  it('对话返回带该块：composable 透传后在助手消息内渲染三件内容', async () => {
    const wrapper = await mountPage()
    chat.mockResolvedValue({
      status: true,
      data: {
        reply: '已点击开关',
        model_name: 'stub-model',
        log_check: { clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }], log: LOG },
      },
    })
    const vm = wrapper.vm as unknown as {
      question: string
      serial: string
      send: () => Promise<void>
    }
    vm.question = '点一下开关'
    vm.serial = 'DEV-1'
    await vm.send()
    await nextTick()

    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain('日志检查')
    expect(block.text()).toContain(CLICK_TIME)
    expect(block.text()).toContain(SHOT)
    expect(block.text()).toContain('switch_off')
  })

  it('无日志证据：只有时间点与截图', async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper, {
      clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }],
      log: null,
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain(CLICK_TIME)
    expect(block.find('[data-testid="step-log-evidence"]').exists()).toBe(false)
  })

  it('无该键（本轮没点击）不渲染该块', async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper)
    expect(wrapper.find('[data-testid="step-log-check"]').exists()).toBe(false)
  })

  it('未截图时如实标注，不借用其它截图', async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper, {
      clicks: [{ action_time: CLICK_TIME, screenshot_path: '' }],
      log: null,
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.text()).toContain('该次点击后未截图')
    expect(block.find('[data-testid="log-check-screenshot"]').exists()).toBe(false)
  })

  it('该块只读：没有按钮与输入控件', async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper, {
      clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }],
      log: LOG,
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.findAll('button').length).toBe(0)
    expect(block.findAll('input').length).toBe(0)
  })
})
