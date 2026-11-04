/**
 * [P0] 必测 — 任务详情四层耗时展示
 * 目录：tests/task-list/p0/
 *
 * 覆盖 spec「详情页展示四层耗时」：用例行、步骤行、执行/验收块头各一处，
 * 运行中显示「进行中」，缺失或 0 不渲染。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { mount, flushPromises, type VueWrapper } from "@vue/test-utils"

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
import { formatDurationMs } from "@/modules/task-list/helpers/report-steps"

/** 一条用例、两步、每步一执行一验收的完成态报告 */
function makeReport(options: { running?: boolean } = {}) {
  const running = Boolean(options.running)
  const rounds = [
    {
      round_id: 0,
      role: "executor_role",
      role_kind: "executor",
      model: "deepseek-flash",
      step_seq: 1,
      attempt: 1,
      subject: "启动应用",
      blocks: [],
      verdict: null,
      model_ms: 38000,
      running: false,
    },
    {
      round_id: 1,
      role: "verifier_role",
      role_kind: "verifier",
      model: "deepseek-flash",
      step_seq: 1,
      attempt: 1,
      subject: "启动应用",
      blocks: [],
      verdict: { passed: true, message: "已启动" },
      model_ms: 3900,
      running,
    },
  ]
  return {
    status: true,
    data: {
      task: { id: 1, title: "耗时任务", status: running ? "running" : "completed", cost_total: 0 },
      rounds,
      cases: [
        {
          title: "用例甲",
          outcome: running ? "未完成" : "PASS",
          steps: [
            {
              seq: 1,
              action: "启动应用",
              expected: "前台为本应用",
              outcome: "PASS",
              duration_ms: 192000,
              model_ms: 41900,
              tool_ms: 98000,
              idle_ms: 52100,
              interrupt: "",
            },
            {
              seq: 2,
              action: "点击设备",
              expected: "出现设备列表",
              outcome: "PASS",
              duration_ms: 42000,
              interrupt: "",
            },
          ],
          round_ids: [0, 1],
          duration_ms: 250000,
          running,
        },
      ],
      conclusion: { outcome: running ? "" : "PASS" },
    },
  }
}

describe("[P0] formatDurationMs", () => {
  it("三档紧凑格式", () => {
    expect(formatDurationMs(42000)).toBe("42s")
    expect(formatDurationMs(192000)).toBe("3m12s")
    expect(formatDurationMs(3720000)).toBe("1h02m")
  })

  it("0、负数与不足 1 秒返回空串", () => {
    expect(formatDurationMs(0)).toBe("")
    expect(formatDurationMs(-5)).toBe("")
    expect(formatDurationMs(undefined)).toBe("")
    expect(formatDurationMs(400)).toBe("")
  })
})

describe("[P0] 任务详情四层耗时展示", () => {
  let wrapper: VueWrapper | null = null

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
  })

  it("用例行与步骤行显示耗时", async () => {
    mocks.getTaskReport.mockResolvedValue(makeReport())
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    expect(wrapper.find(".flow-case__duration").text()).toBe("4m10s")

    const stepDurations = wrapper.findAll(".flow-step__duration").map((node) => node.text())
    expect(stepDurations).toEqual(["3m12s", "42s"])
  })

  it("耗时排在结果徽标之前", async () => {
    mocks.getTaskReport.mockResolvedValue(makeReport())
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    const caseTitle = wrapper.find(".flow-case__title").element as HTMLElement
    const classes = Array.from(caseTitle.children).map((child) => child.className)
    expect(classes.indexOf("flow-case__duration")).toBeGreaterThan(-1)
    expect(classes.indexOf("flow-case__duration")).toBeLessThan(
      classes.findIndex((name) => name.includes("badge")),
    )

    const stepTitle = wrapper.find(".flow-step__title").element as HTMLElement
    const stepClasses = Array.from(stepTitle.children).map((child) => child.className)
    expect(stepClasses.findIndex((name) => name.includes("flow-step__duration"))).toBeLessThan(
      stepClasses.findIndex((name) => name.includes("flow-step__badge")),
    )
  })

  it("执行与验收块头显示模型耗时", async () => {
    mocks.getTaskReport.mockResolvedValue(makeReport())
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    await wrapper.findAll(".flow-step__title")[0].trigger("click")

    const durations = wrapper.findAll(".flow-proc__duration").map((node) => node.text())
    expect(durations).toEqual(["模型 38s", "模型 4s"])
  })

  it("运行中显示进行中而不是数字", async () => {
    mocks.getTaskReport.mockResolvedValue(makeReport({ running: true }))
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    expect(wrapper.find(".flow-case__duration").text()).toBe("进行中")

    await wrapper.findAll(".flow-step__title")[0].trigger("click")
    const durations = wrapper.findAll(".flow-proc__duration").map((node) => node.text())
    expect(durations).toEqual(["模型 38s", "进行中"])
  })

  it("缺耗时不渲染 0s", async () => {
    const report = makeReport()
    report.data.cases[0].duration_ms = 0
    report.data.cases[0].steps[0].duration_ms = 0
    report.data.rounds[0].model_ms = 0
    mocks.getTaskReport.mockResolvedValue(report)
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    expect(wrapper.find(".flow-case__duration").exists()).toBe(false)

    await wrapper.findAll(".flow-step__title")[0].trigger("click")
    expect(wrapper.text()).not.toContain("0s")
  })

  it("步骤行给出模型 / 工具 / 空档三项耗时", async () => {
    mocks.getTaskReport.mockResolvedValue(makeReport())
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    const costs = wrapper.findAll(".flow-step__cost").map((node) => node.text())
    expect(costs).toEqual(["模型 42s", "工具 1m38s", "空档 52s"])
  })

  it("三项为 0 时不渲染空档与工具徽标", async () => {
    const report = makeReport()
    const secondStep = report.data.cases[0].steps[1]
    secondStep.model_ms = 0
    secondStep.tool_ms = 0
    secondStep.idle_ms = 0
    mocks.getTaskReport.mockResolvedValue(report)
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    const rows = wrapper.findAll(".flow-step")
    expect(rows[1].findAll(".flow-step__cost")).toHaveLength(0)
    expect(rows[0].findAll(".flow-step__cost")).toHaveLength(3)
  })

  it("日志中断的步骤标出「日志中断」并把原因挂在 title 上", async () => {
    const report = makeReport({ running: true })
    report.data.cases[0].steps[0].interrupt = "日志为空，请检查断后是否正确连接，此轮执行终止"
    mocks.getTaskReport.mockResolvedValue(report)
    wrapper = mount(TaskDetailPage)
    await flushPromises()

    const badge = wrapper.find('[data-test="step-interrupt"]')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe("日志中断")
    expect(badge.attributes("title")).toContain("日志为空")

    // 没有打断的步骤不渲染该标记
    const rows = wrapper.findAll(".flow-step")
    expect(rows[1].findAll('[data-test="step-interrupt"]')).toHaveLength(0)
  })
})
