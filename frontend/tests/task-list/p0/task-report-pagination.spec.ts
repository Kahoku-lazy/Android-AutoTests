import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"

/**
 * 任务详情：步骤全量渲染，页面不再分页。
 *
 * 原用例断言「每页 20 个轮次」；折叠单位改成步骤后分页取消，
 * 这里改为断言 25 个步骤全部出现、且没有任何翻页控件。
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

const STEP_COUNT = 25

function buildSteps() {
  return Array.from({ length: STEP_COUNT }, (_, index) => ({
    seq: index + 1,
    action: `第 ${index + 1} 步动作`,
    expected: `第 ${index + 1} 步预期`,
    outcome: "PASS",
  }))
}

function buildRounds() {
  return Array.from({ length: STEP_COUNT * 2 }, (_, index) => {
    const seq = Math.floor(index / 2) + 1
    const isVerifier = index % 2 === 1
    return {
      round_id: index,
      role: isVerifier ? "verifier_role" : "executor_role",
      role_kind: isVerifier ? "verifier" : "executor",
      model: "deepseek-flash",
      step_seq: seq,
      attempt: 1,
      subject: `第 ${seq} 步动作`,
      handover: "",
      verdict: isVerifier ? { passed: true, message: "通过" } : null,
      blocks: [],
    }
  })
}

function reportData() {
  const rounds = buildRounds()
  return {
    status: true,
    data: {
      task: { id: 1, title: "T", status: "completed", cost_total: 0 },
      rounds,
      cases: [
        {
          title: "长用例",
          outcome: "PASS",
          steps: buildSteps(),
          round_ids: rounds.map((item) => item.round_id),
        },
      ],
      conclusion: { outcome: "PASS" },
    },
  }
}

describe("任务详情步骤不分页", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("25 个步骤全部渲染，且没有翻页控件", async () => {
    mocks.getTaskReport.mockResolvedValue(reportData())
    const wrapper = mount(TaskDetailPage)
    await flushPromises()

    expect(wrapper.findAll(".flow-step")).toHaveLength(STEP_COUNT)
    expect(wrapper.text()).not.toContain("上一页")
    expect(wrapper.text()).not.toContain("下一页")
    expect(wrapper.find(".flow-pager").exists()).toBe(false)
  })

  it("每个步骤的折叠目标都存在，且默认关闭", async () => {
    mocks.getTaskReport.mockResolvedValue(reportData())
    const wrapper = mount(TaskDetailPage)
    await flushPromises()

    const titles = wrapper.findAll(".flow-step__title")
    expect(titles).toHaveLength(STEP_COUNT)
    for (const title of titles) {
      expect(title.attributes("aria-expanded")).toBe("false")
      expect(title.attributes("aria-controls")).toMatch(/^flow-step-body-/)
    }
    expect(wrapper.findAll(".flow-step__body")).toHaveLength(0)
  })

  it("展开某一步只出现该步的展开体", async () => {
    mocks.getTaskReport.mockResolvedValue(reportData())
    const wrapper = mount(TaskDetailPage)
    await flushPromises()

    await wrapper.findAll(".flow-step__title")[1].trigger("click")
    expect(wrapper.findAll(".flow-step__body")).toHaveLength(1)
    expect(wrapper.findAll(".flow-step__body")[0].attributes("id")).toBe(
      wrapper.findAll(".flow-step__title")[1].attributes("aria-controls"),
    )
  })
})
