/**
 * [P0] 必测 — 任务尝试卡片（执行结果常显 / 截图不折叠 / Agent 默认收起）
 * 目录：tests/ai-assistant/p0/
 */
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"
import TaskAttemptCard from "@/modules/ai-assistant/components/TaskAttemptCard.vue"
import type { TaskStepAttempt } from "@/modules/ai-assistant/helpers/task-detail"

const stubs = {
  "el-collapse": {
    template: '<div class="el-collapse" data-testid="agent-collapse"><slot /></div>',
  },
  "el-collapse-item": {
    props: ["title", "name"],
    template:
      '<div class="el-collapse-item" :data-name="name">' +
      '<span class="el-collapse-item__title">{{ title }}</span>' +
      '<div class="el-collapse-item__wrap" style="display:none"><slot /></div>' +
      "</div>",
  },
  "el-image": {
    props: ["src"],
    template: '<img class="el-image" :src="src" v-bind="$attrs" />',
  },
}

function makeAttempt(overrides: Partial<TaskStepAttempt> = {}): TaskStepAttempt {
  return {
    loop: 1,
    executorResult: "pass",
    executorMessage: "已点击按钮",
    verifierResult: "pass",
    actual: "页面已跳转",
    screenshotUrl: "/media/shots/verify-1.png",
    executorTrace: {
      input: "执行：点击登录",
      thinking: ["先找登录按钮"],
      tools: [{ type: "call", name: "tap", input: "登录" }],
      text: "点击完成",
    },
    verifierTrace: {
      input: "验收：进入首页",
      thinking: ["检查标题"],
      text: "验收通过",
    },
    ...overrides,
  }
}

function mountCard(attempt?: Partial<TaskStepAttempt>, maxLoops = 3) {
  return mount(TaskAttemptCard, {
    props: {
      attempt: makeAttempt(attempt),
      maxLoops,
    },
    global: { stubs },
  })
}

describe("[P0] TaskAttemptCard", () => {
  it("执行结果常显：含执行/验收结论，且不在 collapse 内", () => {
    const wrapper = mountCard()
    const result = wrapper.find('[data-testid="attempt-result"]')
    expect(result.exists()).toBe(true)
    expect(result.text()).toContain("执行")
    expect(result.text()).toContain("pass")
    expect(result.text()).toContain("已点击按钮")
    expect(result.text()).toContain("验收")
    expect(result.text()).toContain("页面已跳转")
    expect(result.find(".el-collapse").exists()).toBe(false)
    expect(wrapper.find('[data-testid="agent-collapse"]').exists()).toBe(true)
  })

  it("有截图时 el-image 常显在结果区", () => {
    const wrapper = mountCard()
    const shot = wrapper.find('[data-testid="attempt-screenshot"]')
    expect(shot.exists()).toBe(true)
    expect(shot.attributes("src")).toBe("/media/shots/verify-1.png")
    const inResult = wrapper.find(
      '[data-testid="attempt-result"] [data-testid="attempt-screenshot"]',
    )
    expect(inResult.exists()).toBe(true)
  })

  it("新执行契约：点击前时间与点击后截图路径可见，截图可点开", () => {
    const wrapper = mountCard({
      executorClickTimer: "2026-09-28 17:01:12.645",
      executorScreenshotPath: "ai_tasks/9/s1_l1.jpg",
      executorScreenshotUrl: "/media/ai_tasks/9/s1_l1.jpg",
    })
    const result = wrapper.find('[data-testid="attempt-result"]')
    expect(result.text()).toContain("点击前时间")
    expect(result.text()).toContain("2026-09-28 17:01:12.645")
    expect(result.text()).toContain("点击后截图")
    expect(result.text()).toContain("ai_tasks/9/s1_l1.jpg")
    const shot = wrapper.find('[data-testid="attempt-executor-screenshot"]')
    expect(shot.exists()).toBe(true)
    expect(shot.attributes("src")).toBe("/media/ai_tasks/9/s1_l1.jpg")
  })

  it("新执行契约未截图时如实标注，不渲染图片", () => {
    const wrapper = mountCard({
      executorClickTimer: "2026-09-28 17:01:12.645",
      executorScreenshotPath: "",
      executorScreenshotUrl: "",
    })
    const none = wrapper.find('[data-testid="attempt-executor-shot-none"]')
    expect(none.exists()).toBe(true)
    expect(none.text()).toBe("该步未截图")
    expect(wrapper.find('[data-testid="attempt-executor-screenshot"]').exists()).toBe(false)
  })

  it("存量旧记录：没有点击证据行，说明文字照旧显示", () => {
    const wrapper = mountCard()
    const result = wrapper.find('[data-testid="attempt-result"]')
    expect(result.text()).toContain("已点击按钮")
    expect(result.find('[data-testid="attempt-executor-click-timer"]').exists()).toBe(false)
    expect(result.find('[data-testid="attempt-executor-shot-path"]').exists()).toBe(false)
    expect(result.find('[data-testid="attempt-executor-shot-none"]').exists()).toBe(false)
  })

  it("执行结果段只读：没有按钮与输入控件", () => {
    const wrapper = mountCard({
      executorClickTimer: "2026-09-28 17:01:12.645",
      executorScreenshotPath: "a/b.jpg",
      executorScreenshotUrl: "/media/a/b.jpg",
    })
    const result = wrapper.find('[data-testid="attempt-result"]')
    expect(result.findAll("button").length).toBe(0)
    expect(result.findAll("input").length).toBe(0)
  })

  it("Agent 折叠默认未展开", () => {
    const wrapper = mountCard()
    const collapse = wrapper.find('[data-testid="agent-collapse"]')
    expect(collapse.exists()).toBe(true)
    const wraps = collapse.findAll(".el-collapse-item__wrap")
    expect(wraps.length).toBeGreaterThan(0)
    wraps.forEach((w) => {
      const style = (w.attributes("style") || "").replace(/\s/g, "")
      expect(style).toContain("display:none")
    })
    expect(collapse.text()).toContain("Executor Agent Info")
    expect(collapse.text()).toContain("Verifier Agent Info")
  })

  it("标题与正文 class 分离", () => {
    const wrapper = mountCard()
    expect(wrapper.find(".tac__title").exists()).toBe(true)
    expect(wrapper.find(".tac-result__title").exists()).toBe(true)
    expect(wrapper.find(".tac-result__row").exists()).toBe(true)
    expect(wrapper.find(".tac-result__label").exists()).toBe(true)
  })

  it("日志证据摘要常显在尝试卡片内（不在 Agent 折叠块里）", () => {
    const wrapper = mountCard({
      logEvidence: {
        conclusion: "hit",
        window_line_count: 3,
        hits: [
          {
            keyword: "switch_off",
            grade: "strong",
            count: 1,
            features: [{ id: 1, module: "设备开关", feature: "关闭设备成功" }],
          },
        ],
      },
    })
    const block = wrapper.find('[data-testid="step-log-evidence"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain("设备日志证据")
    expect(block.text()).toContain("强证据")
    expect(block.text()).toContain("switch_off")
    expect(block.text()).toContain("关闭设备成功")
    expect(block.find('[data-testid="log-evidence-summary"]').exists()).toBe(true)
  })

  it("无日志证据时给出一行可读说明", () => {
    const wrapper = mountCard()
    const empty = wrapper.find('[data-testid="log-evidence-empty"]')
    expect(empty.exists()).toBe(true)
    expect(empty.text()).toContain("未采集到设备日志证据")
    expect(wrapper.find('[data-testid="log-evidence-summary"]').exists()).toBe(false)
  })

  it("未命中时摘要给出结论与窗口行数", () => {
    const wrapper = mountCard({
      logEvidence: { conclusion: "no_hit", window_line_count: 3 },
    })
    const conclusion = wrapper.find('[data-testid="log-evidence-conclusion"]')
    expect(conclusion.exists()).toBe(true)
    expect(conclusion.text()).toContain("未命中")
    expect(conclusion.text()).toContain("3 行")
  })

  it("详情里同毫秒合并条按发生顺序换行呈现", () => {
    const wrapper = mountCard({
      logEvidence: {
        conclusion: "hit",
        hits: [{ keyword: "switch_off", grade: "strong", count: 1 }],
        lines: [{ timestamp: "T", source: "tcp", text: "request\nstart\nswitch_off" }],
      },
    })
    const rows = wrapper.findAll(".sle-row__text")
    expect(rows.length).toBeGreaterThan(0)
    expect(rows[rows.length - 1].text().split("\n")).toEqual(["request", "start", "switch_off"])
  })

  it("证据区块只读：没有按钮与输入控件", () => {
    const wrapper = mountCard({
      logEvidence: {
        conclusion: "hit",
        hits: [{ keyword: "switch_off", grade: "strong", count: 1 }],
        lines: [{ timestamp: "T", source: "tcp", text: "x" }],
      },
    })
    const block = wrapper.find('[data-testid="step-log-evidence"]')
    expect(block.findAll("button").length).toBe(0)
    expect(block.findAll("input").length).toBe(0)
  })
})
