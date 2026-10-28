import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"

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

/** 报告里的一轮：默认执行角色，可按需改成验收角色并带判决。 */
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

function reportData(rounds: Array<Record<string, unknown>>) {
  return {
    status: true,
    data: {
      task: { id: 1, title: "T", status: "completed", cost_total: 0 },
      rounds,
      cases: [
        {
          title: "测试 Agent 功能",
          outcome: "PASS",
          round_ids: rounds.map((r) => r.round_id),
        },
      ],
      conclusion: { outcome: "PASS" },
    },
  }
}

async function mountWith(rounds: Array<Record<string, unknown>>) {
  mocks.getTaskReport.mockResolvedValue(reportData(rounds))
  const wrapper = mount(TaskDetailPage)
  await flushPromises()
  return wrapper
}

/** 第 i 轮的标题文本（不含行首的折叠标记）。 */
function titleTexts(wrapper: ReturnType<typeof mount>) {
  return wrapper.findAll(".flow-round__text").map((item) => item.text())
}

describe("任务详情轮次标题", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("执行轮：序号 + ➡️ + 角色徽章，不再写类别与模型名", async () => {
    const wrapper = await mountWith([round()])
    const [title] = titleTexts(wrapper)

    expect(title).toContain("1.")
    expect(title).toContain("➡️")
    expect(title).toContain("executor_role")
    expect(title).toContain("：启动 govee 应用")
    for (const banned of ["执行模型", "验收模型", "步骤", "deepseek-flash"]) {
      expect(title).not.toContain(banned)
    }
  })

  it("验收轮不占序号，以结果标记开头，且不挂 PASS / FAIL 徽章", async () => {
    const wrapper = await mountWith([
      round(),
      round({
        round_id: 1,
        role: "verifier_role",
        role_kind: "verifier",
        subject: "前台为 govee",
        verdict: { passed: true, message: "已在前台" },
      }),
      round({ round_id: 2, step_seq: 2, subject: "关闭 APP" }),
    ])

    const titles = titleTexts(wrapper)
    expect(titles[1].startsWith("✅")).toBe(true)
    expect(titles[1]).toContain("verifier_role")
    expect(titles[1]).toContain("：前台为 govee")
    expect(titles[2].startsWith("2.")).toBe(true)

    // 验收轮没有数字序号：以 ✅ 开头即说明序号位置被结果标记接管
    expect(/^\d/.test(titles[1])).toBe(false)

    // 判决只由 ✅ 表示：标题里既无 PASS 文字，也只有一个徽章（角色名）
    expect(titles[1]).not.toContain("PASS")
    const verifier = wrapper.findAll(".flow-round")[1]
    expect(verifier.findAll(".flow-round__title .badge").map((b) => b.text())).toEqual([
      "verifier_role",
    ])
  })

  it("验收轮失败用 ❌，不写 FAIL 文字", async () => {
    const wrapper = await mountWith([
      round({
        role: "verifier_role",
        role_kind: "verifier",
        subject: "仍在首页",
        verdict: { passed: false, message: "未进入列表" },
      }),
    ])
    const [title] = titleTexts(wrapper)
    expect(title.startsWith("❌")).toBe(true)
    expect(title).not.toContain("FAIL")
  })

  it("尚无判决的验收轮没有 ✅ / ❌，也不带序号", async () => {
    const wrapper = await mountWith([
      round({ role: "verifier_role", role_kind: "verifier", subject: "前台为 govee" }),
    ])
    const [title] = titleTexts(wrapper)
    expect(title).not.toContain("✅")
    expect(title).not.toContain("❌")
    expect(/^\d/.test(title)).toBe(false)
    expect(title).toContain("：前台为 govee")
  })

  it("两角色徽章配色不同（执行 / 验收各一个类）", async () => {
    const wrapper = await mountWith([
      round(),
      round({
        round_id: 1,
        role: "verifier_role",
        role_kind: "verifier",
        verdict: { passed: true },
      }),
    ])
    const badges = wrapper.findAll(".flow-round__title .badge-role")
    expect(badges[0].classes()).toContain("is-executor")
    expect(badges[1].classes()).toContain("is-verifier")
  })

  it("重试轮序号与首次相同并标第几次", async () => {
    const wrapper = await mountWith([
      round(),
      round({
        round_id: 1,
        role: "verifier_role",
        role_kind: "verifier",
        verdict: { passed: false, message: "未就绪" },
      }),
      round({ round_id: 2, attempt: 2 }),
    ])
    const titles = titleTexts(wrapper)
    expect(titles[2]).toContain("第 2 次")
    expect(titles[2].startsWith("1.")).toBe(true)
  })

  it("角色名为空的存量轮次不渲染角色徽章", async () => {
    const wrapper = await mountWith([round({ role: "", subject: "点击开关" })])
    const title = wrapper.get(".flow-round__title")
    expect(title.find(".badge-role").exists()).toBe(false)
    expect(title.text()).toContain("➡️")
    expect(title.text()).toContain("：点击开关")
  })
})
