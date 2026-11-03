import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"

/**
 * 任务详情：步骤行与按次展开。
 *
 * 取代原「轮次标题」用例——折叠单位由轮次改为步骤后，
 * 断言对象变成步骤行的序号/动作/结果徽标与展开体里的次数标签。
 */

const mocks = vi.hoisted(() => ({
  getTaskReport: vi.fn(),
  push: vi.fn(),
}))

vi.mock("@/modules/task-list/api/tasks", () => ({
  getTaskReport: mocks.getTaskReport,
}))

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { id: "1" } }),
  useRouter: () => ({ push: mocks.push }),
}))

import TaskDetailPage from "@/modules/task-list/TaskDetailPage.vue"

/** 一轮：默认执行角色、第 1 次，可按需改成验收角色并带判决 */
function round(overrides: Record<string, unknown> = {}) {
  return {
    round_id: 0,
    role: "executor_role",
    role_kind: "executor",
    model: "deepseek-flash",
    step_seq: 1,
    attempt: 1,
    subject: "启动 govee 应用",
    handover: "",
    verdict: null,
    blocks: [],
    ...overrides,
  }
}

function verifier(overrides: Record<string, unknown> = {}) {
  return round({
    role: "verifier_role",
    role_kind: "verifier",
    subject: "前台为 govee",
    verdict: { passed: true, message: "已在前台" },
    ...overrides,
  })
}

function reportData(
  rounds: Array<Record<string, unknown>>,
  steps: Array<Record<string, unknown>>,
) {
  return {
    status: true,
    data: {
      task: { id: 1, title: "T", status: "completed", cost_total: 0 },
      rounds,
      cases: [
        {
          title: "测试 Agent 功能",
          outcome: "PASS",
          steps,
          round_ids: rounds.map((item) => item.round_id),
        },
      ],
      conclusion: { outcome: "PASS" },
    },
  }
}

async function mountWith(
  rounds: Array<Record<string, unknown>>,
  steps: Array<Record<string, unknown>>,
) {
  mocks.getTaskReport.mockResolvedValue(reportData(rounds, steps))
  const wrapper = mount(TaskDetailPage)
  await flushPromises()
  return wrapper
}

const oneStep = [{ seq: 1, action: "启动 govee 应用", expected: "前台为 govee", outcome: "PASS" }]

describe("任务详情步骤行", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("步骤行：序号 + 动作 + 结果徽标，动作只出现一次", async () => {
    const wrapper = await mountWith([round(), verifier({ round_id: 1 })], oneStep)

    const steps = wrapper.findAll(".flow-step")
    expect(steps).toHaveLength(1)

    const title = wrapper.get(".flow-step__title")
    expect(title.text()).toContain("1.")
    expect(title.text()).toContain("启动 govee 应用")
    expect(title.find(".flow-step__badge").text()).toBe("PASS")
    // 步骤行不再出现模型名与角色类别文字
    expect(title.text()).not.toContain("deepseek-flash")
    expect(title.text()).not.toContain("执行模型")

    await wrapper.get(".flow-step__title").trigger("click")
    const body = wrapper.get(".flow-step__body")
    // 动作不再在展开体里复述
    expect(body.text()).not.toContain("启动 govee 应用")
  })

  it("结果只由步骤徽标表示，验收标记只出现在验收过程头部", async () => {
    const wrapper = await mountWith([round(), verifier({ round_id: 1 })], oneStep)

    expect(wrapper.get(".flow-step__title").text()).not.toContain("✅")

    await wrapper.get(".flow-step__title").trigger("click")
    const verifierProc = wrapper.get(".flow-proc.is-verifier")
    expect(verifierProc.get(".flow-proc__verdict").text()).toBe("✅")
  })

  it("验收驳回时过程头部用 ❌", async () => {
    const wrapper = await mountWith(
      [verifier({ verdict: { passed: false, message: "未进入列表" } })],
      [{ seq: 1, action: "打开列表", outcome: "FAIL" }],
    )
    await wrapper.get(".flow-step__title").trigger("click")

    expect(wrapper.get(".flow-proc__verdict").text()).toBe("❌")
    expect(wrapper.get(".flow-step__badge").text()).toBe("FAIL")
  })

  it("两个过程按角色分色（执行 / 验收各一个类）", async () => {
    const wrapper = await mountWith([round(), verifier({ round_id: 1 })], oneStep)
    await wrapper.get(".flow-step__title").trigger("click")

    const roles = wrapper.findAll(".flow-proc__role")
    expect(roles[0].classes()).toContain("is-executor")
    expect(roles[0].text()).toBe("executor_role")
    expect(roles[1].classes()).toContain("is-verifier")
    expect(roles[1].text()).toBe("verifier_role")
  })

  it("重试按次分块，块头是次数标签", async () => {
    const wrapper = await mountWith(
      [
        round({ round_id: 0, attempt: 1 }),
        verifier({ round_id: 1, attempt: 1, verdict: { passed: false, message: "未就绪" } }),
        round({ round_id: 2, attempt: 2 }),
        verifier({ round_id: 3, attempt: 2 }),
      ],
      [{ seq: 1, action: "设置定时", outcome: "PASS" }],
    )
    await wrapper.get(".flow-step__title").trigger("click")

    const tags = wrapper.findAll(".flow-attempt__tag")
    expect(tags.map((tag) => tag.text())).toEqual(["第1次", "第2次"])
    expect(tags[0].classes()).toContain("is-fail")
    expect(tags[1].classes()).toContain("is-retry")
    expect(wrapper.findAll(".flow-step")).toHaveLength(1)
  })

  it("角色名为空的存量轮次不渲染角色徽章", async () => {
    const wrapper = await mountWith(
      [round({ role: "", subject: "点击开关" })],
      [{ seq: 1, action: "点击开关", outcome: "PASS" }],
    )
    await wrapper.get(".flow-step__title").trigger("click")

    expect(wrapper.find(".flow-proc__role").exists()).toBe(false)
    expect(wrapper.get(".flow-proc").text()).toContain("执行过程")
  })

  it("默认只展开用例，步骤全部收起", async () => {
    const wrapper = await mountWith([round()], oneStep)

    expect(wrapper.findAll(".flow-step")).toHaveLength(1)
    expect(wrapper.find(".flow-step__body").exists()).toBe(false)
    expect(wrapper.get(".flow-step__title").attributes("aria-expanded")).toBe("false")
  })

  it("展开步骤后只见块头，过程块默认收起", async () => {
    const wrapper = await mountWith([round(), verifier({ round_id: 1 })], oneStep)
    await wrapper.get(".flow-step__title").trigger("click")

    expect(wrapper.findAll(".flow-proc")).toHaveLength(2)
    expect(wrapper.findAll(".flow-attempt__head")).toHaveLength(1)
    expect(wrapper.findAll(".flow-timeline")).toHaveLength(0)
    for (const head of wrapper.findAll(".flow-proc__head")) {
      expect(head.attributes("aria-expanded")).toBe("false")
    }
  })

  it("点开执行过程才渲染时间线，验收过程仍收起", async () => {
    const blocks = [
      {
        phase: "执行阶段",
        title: "执行阶段",
        items: [
          { seq: 1, label: "工具调用 · tap_device_screen", detail: '{"x":720}', time: "2026-11-03T14:32:44+08:00" },
        ],
      },
    ]
    const wrapper = await mountWith(
      [round({ blocks }), verifier({ round_id: 1, blocks })],
      oneStep,
    )
    await wrapper.get(".flow-step__title").trigger("click")

    const heads = wrapper.findAll(".flow-proc__head")
    await heads[0].trigger("click")

    expect(wrapper.findAll(".flow-timeline")).toHaveLength(1)
    expect(wrapper.get(".flow-proc.is-executor").find(".flow-timeline").exists()).toBe(true)
    expect(wrapper.get(".flow-proc.is-verifier").find(".flow-timeline").exists()).toBe(false)
    expect(heads[0].attributes("aria-expanded")).toBe("true")
    expect(heads[1].attributes("aria-expanded")).toBe("false")
  })

  it("收起尝试块带走其两个过程，另一次尝试不受影响", async () => {
    const wrapper = await mountWith(
      [
        round({ round_id: 0, attempt: 1 }),
        verifier({ round_id: 1, attempt: 1 }),
        round({ round_id: 2, attempt: 2 }),
        verifier({ round_id: 3, attempt: 2 }),
      ],
      [{ seq: 1, action: "设置定时", outcome: "PASS" }],
    )
    await wrapper.get(".flow-step__title").trigger("click")

    expect(wrapper.findAll(".flow-attempt__body")).toHaveLength(2)
    await wrapper.findAll(".flow-attempt__head")[0].trigger("click")

    const bodies = wrapper.findAll(".flow-attempt__body")
    expect(bodies).toHaveLength(1)
    expect(bodies[0].attributes("id")).toBe(wrapper.findAll(".flow-attempt__head")[1].attributes("aria-controls"))
    expect(wrapper.findAll(".flow-proc")).toHaveLength(2)
  })

  it("验收过程收起时头部仍显示判决与结论摘要", async () => {
    const wrapper = await mountWith(
      [verifier({ verdict: { passed: true, message: "已在前台，与预期一致" } })],
      oneStep,
    )
    await wrapper.get(".flow-step__title").trigger("click")

    const verifierProc = wrapper.get(".flow-proc.is-verifier")
    expect(verifierProc.get(".flow-proc__verdict").text()).toBe("✅")
    expect(verifierProc.get(".flow-proc__summary").text()).toBe("已在前台，与预期一致")
    expect(verifierProc.find(".flow-proc__body").exists()).toBe(false)
  })
})
