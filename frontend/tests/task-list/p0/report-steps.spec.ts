import { describe, expect, it } from "vitest"
import {
  attemptVerdict,
  caseStepViews,
  formatClock,
  type StepView,
} from "@/modules/task-list/helpers/report-steps"
import type { TaskReportCase, TaskReportRound } from "@/shared/types/ai"

/** 一轮：默认执行角色、第 1 次，可按需改成验收角色并带判决 */
function round(overrides: Partial<TaskReportRound> = {}): TaskReportRound {
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

function verifier(overrides: Partial<TaskReportRound> = {}): TaskReportRound {
  return round({
    role: "verifier_role",
    role_kind: "verifier",
    subject: "前台为 govee",
    verdict: { passed: true, message: "已在前台" },
    ...overrides,
  })
}

/** 用轮次构造 case + 索引；round_ids 默认全部 */
function build(
  rounds: TaskReportRound[],
  caseOverrides: Partial<TaskReportCase> = {},
): { steps: StepView[]; caseItem: TaskReportCase } {
  const caseItem: TaskReportCase = {
    title: "定时功能",
    outcome: "PASS",
    round_ids: rounds.map((item) => item.round_id),
    ...caseOverrides,
  }
  const roundsById = new Map(rounds.map((item) => [item.round_id, item]))
  return { steps: caseStepViews(caseItem, roundsById), caseItem }
}

const declared = (seq: number, action: string, outcome = "PASS") => ({ seq, action, outcome })

describe("caseStepViews：按步骤归并", () => {
  it("执行轮与验收轮收进同一步，执行在前", () => {
    const rounds = [round({ round_id: 0 }), verifier({ round_id: 1 })]
    const { steps } = build(rounds, {
      steps: [declared(1, "启动 govee 应用")],
    })

    expect(steps).toHaveLength(1)
    expect(steps[0].action).toBe("启动 govee 应用")
    expect(steps[0].outcome).toBe("PASS")
    expect(steps[0].attempts).toHaveLength(1)
    expect(steps[0].attempts[0].executor.map((run) => run.roundId)).toEqual([0])
    expect(steps[0].attempts[0].verifier.map((run) => run.roundId)).toEqual([1])
  })

  it("验收轮先于执行轮到达时，仍落在同一步的执行之后", () => {
    const rounds = [verifier({ round_id: 0 }), round({ round_id: 1 })]
    const { steps } = build(rounds, { steps: [declared(1, "启动应用")] })

    const attempt = steps[0].attempts[0]
    expect(attempt.executor.map((run) => run.roundId)).toEqual([1])
    expect(attempt.verifier.map((run) => run.roundId)).toEqual([0])
  })

  it("同一步的重试按 attempt 升序分成两次尝试", () => {
    const rounds = [
      round({ round_id: 0, attempt: 1 }),
      verifier({ round_id: 1, attempt: 1, verdict: { passed: false, message: "未就绪" } }),
      round({ round_id: 2, attempt: 2 }),
      verifier({ round_id: 3, attempt: 2 }),
    ]
    const { steps } = build(rounds, { steps: [declared(1, "设置定时")] })

    expect(steps).toHaveLength(1)
    expect(steps[0].attempts.map((item) => item.attempt)).toEqual([1, 2])
    expect(attemptVerdict(steps[0].attempts[0])).toBe(false)
    expect(attemptVerdict(steps[0].attempts[1])).toBe(true)
  })

  it("一次执行配两次验收时，两条验收都在同一尝试里", () => {
    const rounds = [
      round({ round_id: 0 }),
      verifier({ round_id: 1 }),
      verifier({ round_id: 2, verdict: { passed: false, message: "又驳回" } }),
    ]
    const { steps } = build(rounds, { steps: [declared(1, "启动应用")] })

    expect(steps[0].attempts).toHaveLength(1)
    expect(steps[0].attempts[0].verifier).toHaveLength(2)
    expect(attemptVerdict(steps[0].attempts[0])).toBe(false)
  })

  it("没有步骤定义时按 step_seq 生成步骤轴，动作取执行轮的 subject", () => {
    const rounds = [
      round({ round_id: 0, step_seq: 1, subject: "启动应用" }),
      verifier({ round_id: 1, step_seq: 1 }),
      round({ round_id: 2, step_seq: 2, subject: "设置定时" }),
      verifier({ round_id: 3, step_seq: 2, verdict: { passed: false, message: "日志未命中" } }),
    ]
    const { steps } = build(rounds)

    expect(steps.map((step) => step.seq)).toEqual([1, 2])
    expect(steps.map((step) => step.action)).toEqual(["启动应用", "设置定时"])
    expect(steps[1].outcome).toBe("FAIL")
  })

  it("步骤没有轮次时仍保留该步，结果为未执行", () => {
    const rounds = [round({ round_id: 0 })]
    const { steps } = build(rounds, {
      steps: [declared(1, "启动应用"), declared(2, "设置定时", "未执行")],
    })

    expect(steps).toHaveLength(2)
    expect(steps[1].attempts).toEqual([])
    expect(steps[1].outcome).toBe("未执行")
  })

  it("缺少 step_seq 的存量轮次各自成一步，且不丢轮次", () => {
    const rounds = [
      round({ round_id: 0, step_seq: null, subject: "打开应用" }),
      verifier({ round_id: 1, step_seq: null, subject: "前台为 govee" }),
    ]
    const { steps } = build(rounds)

    expect(steps).toHaveLength(2)
    expect(steps.map((step) => step.action)).toEqual(["打开应用", "前台为 govee"])
    expect(steps[0].outcome).toBe("未完成")
    expect(steps[1].outcome).toBe("PASS")
  })

  it("声明步骤之外的轮次补在末尾，不丢内容", () => {
    const rounds = [round({ round_id: 0 }), round({ round_id: 1, step_seq: null, subject: "额外动作" })]
    const { steps } = build(rounds, { steps: [declared(1, "启动应用")] })

    expect(steps).toHaveLength(2)
    expect(steps[1].seq).toBe(2)
    expect(steps[1].action).toBe("额外动作")
  })

  it("没有任何步骤与轮次时返回空数组", () => {
    expect(caseStepViews({ round_ids: [] }, new Map())).toEqual([])
    expect(caseStepViews(null, new Map())).toEqual([])
  })

  it("round_ids 指向不存在的轮次时跳过，不报错", () => {
    const rounds = [round({ round_id: 0 })]
    const caseItem: TaskReportCase = { round_ids: [0, 99], steps: [declared(1, "启动应用")] }
    const steps = caseStepViews(caseItem, new Map(rounds.map((item) => [item.round_id, item])))

    expect(steps).toHaveLength(1)
    expect(steps[0].attempts[0].executor).toHaveLength(1)
  })
})

describe("formatClock", () => {
  it("只取时分秒", () => {
    expect(formatClock("2026-11-03T14:32:27.000+08:00")).toBe("14:32:27")
  })

  it("空值或非法时间返回空串", () => {
    expect(formatClock()).toBe("")
    expect(formatClock("not-a-time")).toBe("")
  })
})
