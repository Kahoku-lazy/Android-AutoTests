/**
 * [P0] 必测 — 调试台的日志检查块（spec: ai-model-debug）
 *
 * 目录：tests/ai-assistant/p0/
 * 断言：① 对话返回带该块 → 页面在助手消息内渲染时间点 / 截图路径 / 命中关键词（含 composable 透传）；
 * ② 无日志证据 → 只有时间点与截图；③ 无该键 → 不渲染该块；
 * ④ 服务端说未截图时如实呈现；⑤ 块内只读。
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import { nextTick } from "vue"

vi.mock("element-plus", () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

vi.mock("vue-router", async () => {
  const { reactive } = await import("vue")
  return {
    useRoute: () => ({ params: reactive({ role: "executor" }) }),
    useRouter: () => ({ push: vi.fn() }),
  }
})

const fetchConfig = vi.fn()
const chat = vi.fn()
const listDevices = vi.fn()

vi.mock("@/modules/ai-assistant/api/toolbox", () => ({
  fetchModelDebugConfig: (...args: unknown[]) => fetchConfig(...args),
  chatWithModelDebug: (...args: unknown[]) => chat(...args),
}))

vi.mock("@/modules/ai-assistant/api/tasks", () => ({
  listDevices: (...args: unknown[]) => listDevices(...args),
}))

import ModelDebugPage from "@/modules/ai-assistant/ModelDebugPage.vue"

const CLICK_TIME = "2026-09-28 10:51:03.219"
const SHOT = "ai_tasks/debug/s1.jpg"

const LOG = {
  conclusion: "hit",
  window_line_count: 2,
  hits: [{ keyword: "switch_off", grade: "strong", count: 1 }],
}

const CONFIG = {
  agent_id: 1,
  agent_name: "调试智能体",
  role: {
    role: "executor",
    label: "执行模型",
    vision: true,
    needs_device: true,
    model: {
      provider: "deepseek",
      model_name: "stub-model",
      has_api_key: true,
      configured: true,
    },
    prompt: "P",
    tools: [],
  },
  skills: { gate_on: false, shared_by_roles: true, items: [] },
}

const stubs = {
  "el-collapse": { template: '<div class="el-collapse"><slot /></div>' },
  "el-collapse-item": {
    props: ["title", "name"],
    template: '<div class="el-collapse-item"><span>{{ title }}</span><slot /></div>',
  },
  "el-select": { template: '<div class="el-select"><slot /></div>' },
  "el-option": { template: '<div class="el-option" />' },
  "el-image": { props: ["src"], template: '<img class="el-image" :src="src" v-bind="$attrs" />' },
  "WorkbenchHeader": { template: '<div class="wb-header" />' },
  "WorkbenchCrumbs": { template: '<div class="wb-crumbs" />' },
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
    role: "assistant",
    content: "已点击开关",
    model_name: "stub-model",
    tool_usage: [{ type: "result", name: "xpath_action", output: '{"clicked": true}' }],
    log_check: logCheck,
  })
  await nextTick()
}

describe("[P0] 调试台日志检查块", () => {
  beforeEach(() => {
    fetchConfig.mockReset()
    chat.mockReset()
    listDevices.mockReset()
  })

  it("对话返回带该块：composable 透传后在助手消息内渲染三件内容", async () => {
    const wrapper = await mountPage()
    chat.mockResolvedValue({
      status: true,
      data: {
        reply: "已点击开关",
        model_name: "stub-model",
        log_check: { clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }], log: LOG },
      },
    })
    const vm = wrapper.vm as unknown as {
      question: string
      serial: string
      send: () => Promise<void>
    }
    vm.question = "点一下开关"
    vm.serial = "DEV-1"
    await vm.send()
    await nextTick()

    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain("日志检查")
    expect(block.text()).toContain(CLICK_TIME)
    expect(block.text()).toContain(SHOT)
    expect(block.text()).toContain("switch_off")
  })

  it("无日志证据：只有时间点与截图", async () => {
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

  it("无该键（本轮没点击）不渲染该块", async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper)
    expect(wrapper.find('[data-testid="step-log-check"]').exists()).toBe(false)
  })

  it("未截图时如实标注，不借用其它截图", async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper, {
      clicks: [{ action_time: CLICK_TIME, screenshot_path: "" }],
      log: null,
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.text()).toContain("该次点击后未截图")
    expect(block.find('[data-testid="log-check-screenshot"]').exists()).toBe(false)
  })

  it("该块只读：没有按钮与输入控件", async () => {
    const wrapper = await mountPage()
    await pushAssistant(wrapper, {
      clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }],
      log: LOG,
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.findAll("button").length).toBe(0)
    expect(block.findAll("input").length).toBe(0)
  })
})

const BASIS = {
  basis_time: "2026-09-29 11:47:04.326",
  from_message: true,
  files: ["D:/logs/H6810_7005.log"],
  note: "",
}

const VERIFIER_LOG = {
  conclusion: "hit",
  window_line_count: 2,
  hits: [
    { keyword: "switch_on", grade: "strong", count: 1, timestamps: ["2026-09-29 11:47:04.687"] },
  ],
}

/** 直接把助手消息塞进页面状态：本条只验证渲染口径 */
async function pushVerifier(
  wrapper: Awaited<ReturnType<typeof mountPage>>,
  payload: { log_evidence?: unknown; log_basis?: unknown },
) {
  const vm = wrapper.vm as unknown as { messages: unknown[] }
  vm.messages.push({
    id: 3,
    role: "assistant",
    content: '{"result": "PASS"}',
    model_name: "stub-model",
    ...payload,
  })
  await nextTick()
}

describe("[P0] 调试台验收日志证据（调试回溯）", () => {
  beforeEach(() => {
    fetchConfig.mockReset()
    chat.mockReset()
    listDevices.mockReset()
  })

  it("对话返回带证据与基准：页面渲染基准说明与命中关键词", async () => {
    const wrapper = await mountPage()
    chat.mockResolvedValue({
      status: true,
      data: {
        reply: '{"result": "PASS"}',
        model_name: "stub-model",
        log_evidence: VERIFIER_LOG,
        log_basis: BASIS,
      },
    })
    const vm = wrapper.vm as unknown as {
      question: string
      serial: string
      send: () => Promise<void>
    }
    vm.question = "验证设备已打开"
    vm.serial = "DEV-1"
    await vm.send()
    await nextTick()

    const basis = wrapper.find('[data-testid="model-debug-log-basis"]')
    expect(basis.exists()).toBe(true)
    expect(basis.text()).toContain("日志证据 · 调试回溯")
    expect(basis.text()).toContain(BASIS.basis_time)
    expect(basis.text()).toContain("消息里的时刻")
    expect(basis.text()).toContain("不是生产步骤的取证窗")

    const evidence = wrapper.find('[data-testid="step-log-evidence"]')
    expect(evidence.exists()).toBe(true)
    expect(evidence.text()).toContain("switch_on")
    expect(evidence.text()).toContain("2026-09-29 11:47:04.687")
  })

  it("取不到日志时给可读原因，不渲染证据块", async () => {
    const wrapper = await mountPage()
    await pushVerifier(wrapper, {
      log_basis: { ...BASIS, from_message: false, files: [], note: "窗口内无日志" },
    })
    const basis = wrapper.find('[data-testid="model-debug-log-basis"]')
    expect(basis.exists()).toBe(true)
    expect(basis.text()).toContain("最近一个取证窗")
    expect(basis.text()).toContain("窗口内无日志")
    expect(wrapper.find('[data-testid="step-log-evidence"]').exists()).toBe(false)
  })

  it("没有该键（如执行角色）时整块不渲染", async () => {
    const wrapper = await mountPage()
    await pushVerifier(wrapper, {})
    expect(wrapper.find('[data-testid="model-debug-log-basis"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="step-log-evidence"]').exists()).toBe(false)
  })

  it("该块只读：没有按钮与输入控件", async () => {
    const wrapper = await mountPage()
    await pushVerifier(wrapper, { log_evidence: VERIFIER_LOG, log_basis: BASIS })
    const basis = wrapper.find('[data-testid="model-debug-log-basis"]')
    const evidence = wrapper.find('[data-testid="step-log-evidence"]')
    expect(basis.findAll("button").length).toBe(0)
    expect(basis.findAll("input").length).toBe(0)
    expect(evidence.findAll("button").length).toBe(0)
    expect(evidence.findAll("input").length).toBe(0)
  })

  it("本轮检查的日志关键词（平台自动填）在证据块内可见", async () => {
    const wrapper = await mountPage()
    chat.mockResolvedValue({
      status: true,
      data: {
        reply: '{"result": "PASS"}',
        model_name: "stub-model",
        log_evidence: VERIFIER_LOG,
        log_basis: BASIS,
        log_assertion_info: "switch_on",
      },
    })
    const vm = wrapper.vm as unknown as {
      question: string
      serial: string
      send: () => Promise<void>
    }
    vm.question = "验证设备已打开"
    vm.serial = "DEV-1"
    await vm.send()
    await nextTick()

    const info = wrapper.find('[data-testid="model-debug-log-assertion-info"]')
    expect(info.exists()).toBe(true)
    expect(info.text()).toContain("本轮检查的日志关键词")
    expect(info.text()).toContain("switch_on")
  })

  it("没有关键词（未检查过日志）时不渲染该行", async () => {
    const wrapper = await mountPage()
    await pushVerifier(wrapper, { log_evidence: VERIFIER_LOG, log_basis: BASIS })
    expect(wrapper.find('[data-testid="model-debug-log-assertion-info"]').exists()).toBe(false)
  })
})
