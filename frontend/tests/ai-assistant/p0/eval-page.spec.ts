import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"
import ElementPlus from "element-plus"
import Evals from "@/modules/ai-assistant/evals.vue"

const api = vi.hoisted(() => ({
  listAssistants: vi.fn(),
  listSopWorkflows: vi.fn(),
  fetchEvalMethods: vi.fn(),
  fetchEvalCases: vi.fn(),
  fetchEvalCandidates: vi.fn(),
  fetchEvalScores: vi.fn(),
  fetchSuiteRuns: vi.fn(),
  fetchEvalReport: vi.fn(async () => "<html></html>"),
  runEval: vi.fn(),
  runSuiteEval: vi.fn(),
  publishAssistant: vi.fn(),
  publishWorkflow: vi.fn(),
  evalReportUrl: (id: number) => `/api/ai/eval-reports/${id}/`,
}))

vi.mock("@/modules/ai-assistant/api/assistants", () => api)
vi.mock("vue-router", () => ({ useRouter: () => ({ push: vi.fn() }) }))

const SCORE = {
  id: 1,
  target_kind: "assistant",
  target_id: "a1",
  prompt_fingerprint: "fp-1",
  source_ref: "",
  judge_model: "deepseek-chat",
  created_at: "2026-11-25T08:00:00Z",
  items: [
    { metric_key: "prompt_quality", score: 0.82, threshold: 0.5, reason: "角色清晰" },
    { metric_key: "handover_quality", score: 0.46, threshold: 0.5, reason: "没写下一步" },
  ],
}

function mountPage() {
  return mount(Evals, {
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

async function pickFirstTarget(wrapper: ReturnType<typeof mountPage>): Promise<void> {
  await wrapper.find(".el-select").trigger("click")
  await flushPromises()
  const option = document.body.querySelector(".el-select-dropdown__item") as HTMLElement | null
  option?.dispatchEvent(new MouseEvent("click", { bubbles: true }))
  await flushPromises()
}

describe("评测页", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ""
    const patched = URL as unknown as {
      createObjectURL?: (blob: Blob) => string
      revokeObjectURL?: (url: string) => void
    }
    patched.createObjectURL = () => "blob:mock-board"
    patched.revokeObjectURL = () => {}
    api.listAssistants.mockResolvedValue([
      {
        assistant_id: "a1",
        display_name: "Android-UI-执行",
        role_name: "执行",
        marker: "teal",
        has_avatar: false,
        release_state: "draft",
      },
    ])
    api.listSopWorkflows.mockResolvedValue([])
    api.fetchEvalMethods.mockResolvedValue([
      {
        key: "prompt_quality",
        name: "提示词质量",
        target: "prompt",
        description: "只看提示词本身",
        criteria: "角色与目标是否明确\n流程是否可执行",
        threshold: 0.5,
      },
    ])
    api.fetchEvalCases.mockResolvedValue([
      {
        id: 5,
        title: "定时功能测试",
        note: "",
        enabled: true,
        steps: [{ action: "点开", assertion: "在详情页", anchor: { page: "首页" } }],
      },
    ])
    api.fetchEvalCandidates.mockResolvedValue([])
    api.fetchEvalScores.mockResolvedValue([SCORE])
    api.fetchSuiteRuns.mockResolvedValue([])
  })

  it("未选对象时只有引导，不渲染结果与口径", async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain("先选一个评测对象")
    expect(wrapper.find(".doc-section").exists()).toBe(false)
    expect(wrapper.find(".eval-fold").exists()).toBe(false)
    expect(wrapper.text()).not.toContain("提示词质量")

    const startButton = wrapper
      .findAll(".eval-bar__tail button")
      .find((node) => node.text().includes("开始评分"))
    expect(startButton?.attributes("disabled")).toBeDefined()
    wrapper.unmount()
  })

  it("页顶没有通栏动作按钮", async () => {
    const wrapper = mountPage()
    await flushPromises()
    const body = wrapper.find(".doc-body").element
    const buttons = Array.from(body.children).filter((node) => node.tagName === "BUTTON")
    expect(buttons).toHaveLength(0)
    wrapper.unmount()
  })

  it("选中对象后出现评分卡、真题集与历史，口径默认收起", async () => {
    const wrapper = mountPage()
    await flushPromises()
    await pickFirstTarget(wrapper)

    expect(wrapper.text()).toContain("评分结果")
    expect(wrapper.text()).toContain("提示词质量")
    expect(wrapper.text()).toContain("0.82")
    expect(wrapper.text()).toContain("未达 0.5")
    expect(wrapper.text()).toContain("真题集")
    expect(wrapper.text()).toContain("定时功能测试")
    expect(wrapper.text()).toContain("评测口径 · 1 项打分规则")
    expect(wrapper.text()).not.toContain("流程是否可执行")

    await wrapper.find(".eval-fold__head").trigger("click")
    expect(wrapper.text()).toContain("流程是否可执行")
    wrapper.unmount()
  })

  it("历史表的分数在指标列，指纹单独成列", async () => {
    const wrapper = mountPage()
    await flushPromises()
    await pickFirstTarget(wrapper)

    expect(wrapper.text()).toContain("提示词质量 0.82")
    expect(wrapper.text()).toContain("交接文本质量 0.46")
    expect(wrapper.text()).toContain("fp-1")
    wrapper.unmount()
  })

  it("未勾选真题时跑真题置灰，勾选后可跑并显示逐条结果", async () => {
    api.fetchSuiteRuns.mockResolvedValue([
      {
        id: 12,
        target_id: "assistant:a1",
        created_at: "2026-11-25T09:00:00Z",
        judge_model: "deepseek-chat",
        method_key: "case_suite",
        report_html: "",
        items: [],
        cases: [
          {
            case_id: "5",
            case_title: "定时功能测试",
            steps_total: 1,
            steps_passed: 1,
            cost_s: 12,
            score: 1,
            reason: "",
          },
        ],
      },
    ])
    const wrapper = mountPage()
    await flushPromises()
    await pickFirstTarget(wrapper)

    const suiteButton = () =>
      wrapper.findAll("button").find((node) => node.text().includes("跑真题"))
    expect(suiteButton()?.attributes("disabled")).toBeDefined()

    const checkbox = wrapper.find(".el-checkbox")
    expect(checkbox.exists()).toBe(true)
    await checkbox.trigger("click")
    await flushPromises()

    expect(suiteButton()?.attributes("disabled")).toBeUndefined()
    expect(wrapper.text()).toContain("最近一次逐条结果")
    expect(wrapper.text()).toContain("1/1")
    expect(wrapper.text()).toContain("达成")
    wrapper.unmount()
  })
})
