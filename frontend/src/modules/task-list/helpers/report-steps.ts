/**
 * 任务详情：把报告里的轮次按步骤归并成「步骤 → 尝试 → 执行/验收」。
 *
 * 数据全部来自 `GET /api/tasks/{id}/report/`，本模块只做纯函数分组：
 * 1. caseStepViews: 用具例的步骤轴挂载轮次，产出可直接渲染的 StepView 列表。
 * 2. formatClock: 事件时间只取时分秒，供步骤展开体内的时间线使用。
 */
import type { TaskReportCase, TaskReportRound, TaskReportStep } from "@/shared/types/ai"

export type RoundKind = "executor" | "verifier"

/** 一步里的一次尝试：该次执行轮与验收轮 */
export interface StepRun {
  roundId: number
  attempt: number
  roleKind: RoundKind
  round: TaskReportRound
}

/** 报告时间统一按北京时间展示：CI 跑在 UTC，用本地时区取小时会整体偏 8 小时 */
const BEIJING_CLOCK = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  hourCycle: "h23",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
})

/** 一次尝试：块头是次数标签，块内执行在前、验收在后 */
export interface AttemptView {
  attempt: number
  executor: StepRun[]
  verifier: StepRun[]
}

/** 一个步骤：步骤行只渲染序号、动作与结果，展开体渲染 attempts */
export interface StepView {
  /** 折叠状态用的稳定键：有 step_seq 用序号，退化时用轮次号 */
  key: string
  seq: number
  action: string
  expected: string
  /** PASS / FAIL / 主动关闭 / 未完成 / 未执行 */
  outcome: string
  /** 该步墙钟耗时（毫秒）；无时间戳为 0，渲染时按缺失处理 */
  durationMs: number
  /** 该步模型调用合计（毫秒） */
  modelMs: number
  /** 该步工具返回合计（毫秒） */
  toolMs: number
  /** 该步空档：墙钟减去模型与工具，不为负（毫秒） */
  idleMs: number
  /** 该步被引擎打断的原因；没有打断时为空串 */
  interrupt: string
  /** 该步仍有未结束的轮次 */
  running: boolean
  attempts: AttemptView[]
}

const OUTCOME_PASS = "PASS"
const OUTCOME_FAIL = "FAIL"
const OUTCOME_UNFINISHED = "未完成"
const OUTCOME_UNEXECUTED = "未执行"

/** 轮次所属角色：优先 role_kind，缺失时按角色名兜底（存量数据） */
function roundKind(round: TaskReportRound): RoundKind {
  const kind = String(round?.role_kind || "").toLowerCase()
  if (kind === "verifier") return "verifier"
  if (kind === "executor") return "executor"
  const name = String(round?.role || round?.role_name || "").toLowerCase()
  return name.includes("verif") ? "verifier" : "executor"
}

/** 轮次的尝试次数：缺失按第 1 次 */
function attemptOf(round: TaskReportRound): number {
  const attempt = Number(round?.attempt)
  return attempt > 0 ? attempt : 1
}

/** 报告里的步骤轴；空值统一成空串，避免模板里再判一次 */
function normalizeSteps(steps?: TaskReportStep[]): TaskReportStep[] {
  return (steps || [])
    .filter((step) => Number(step?.seq) > 0)
    .map((step) => ({
      seq: Number(step.seq),
      action: String(step.action || "").trim(),
      expected: String(step.expected || "").trim(),
      outcome: String(step.outcome || "").trim(),
      duration_ms: Math.max(Number(step.duration_ms) || 0, 0),
      model_ms: Math.max(Number(step.model_ms) || 0, 0),
      tool_ms: Math.max(Number(step.tool_ms) || 0, 0),
      idle_ms: Math.max(Number(step.idle_ms) || 0, 0),
      interrupt: String(step.interrupt || "").trim(),
      running: Boolean(step.running),
    }))
}

/** 无步骤定义时的结果：看该步最后一次带判决的验收 */
function derivedOutcome(group: TaskReportRound[]): string {
  if (!group.length) return OUTCOME_UNEXECUTED
  const judged = group.filter(
    (round) => roundKind(round) === "verifier" && typeof round?.verdict?.passed === "boolean",
  )
  const last = judged[judged.length - 1]
  if (!last) return OUTCOME_UNFINISHED
  return last.verdict?.passed ? OUTCOME_PASS : OUTCOME_FAIL
}

/** 一次尝试的验收是否通过：用于次数标签配色，无判决时为 null */
export function attemptVerdict(attempt: AttemptView): boolean | null {
  const judged = attempt.verifier.filter((run) => typeof run.round?.verdict?.passed === "boolean")
  const last = judged[judged.length - 1]
  if (!last) return null
  return Boolean(last.round.verdict?.passed)
}

/** 把同一步骤的轮次按 attempt 分组，组内执行在前、验收在后 */
function buildAttempts(group: TaskReportRound[]): AttemptView[] {
  const byAttempt = new Map<number, AttemptView>()
  for (const round of group) {
    const attempt = attemptOf(round)
    let view = byAttempt.get(attempt)
    if (!view) {
      view = { attempt, executor: [], verifier: [] }
      byAttempt.set(attempt, view)
    }
    const run: StepRun = {
      roundId: round.round_id,
      attempt,
      roleKind: roundKind(round),
      round,
    }
    if (run.roleKind === "verifier") view.verifier.push(run)
    else view.executor.push(run)
  }
  return [...byAttempt.values()].sort((a, b) => a.attempt - b.attempt)
}

/** 组装一个步骤视图；outcome 优先用后端算好的，缺失时由轮次推导 */
function buildStep(
  key: string,
  seq: number,
  step: {
    action?: string
    expected?: string
    outcome?: string
    duration_ms?: number
    model_ms?: number
    tool_ms?: number
    idle_ms?: number
    interrupt?: string
    running?: boolean
  } | null,
  group: TaskReportRound[],
): StepView {
  return {
    key,
    seq,
    action: String(step?.action || "").trim(),
    expected: String(step?.expected || "").trim(),
    outcome: String(step?.outcome || "").trim() || derivedOutcome(group),
    durationMs: Math.max(Number(step?.duration_ms) || 0, 0),
    modelMs: Math.max(Number(step?.model_ms) || 0, 0),
    toolMs: Math.max(Number(step?.tool_ms) || 0, 0),
    idleMs: Math.max(Number(step?.idle_ms) || 0, 0),
    interrupt: String(step?.interrupt || "").trim(),
    running: Boolean(step?.running),
    attempts: buildAttempts(group),
  }
}

/** 把落不进任何声明步骤的轮次补在末尾，各自成一步（不丢内容） */
function appendOrphans(steps: StepView[], rounds: TaskReportRound[], placed: Set<number>) {
  let extra = Math.max(0, ...steps.map((step) => step.seq))
  for (const round of rounds) {
    if (placed.has(round.round_id)) continue
    extra += 1
    steps.push(buildStep(`r${round.round_id}`, extra, { action: round.subject || "" }, [round]))
  }
}

/**
 * 把一条用例的轮次按步骤归并。
 *
 * Args:
 *   caseItem: 报告 `data.cases[]` 的一项，`round_ids` 指向 `data.rounds`。
 *   roundsById: `round_id → 轮次` 的索引。
 *
 * Returns:
 *   按步骤号升序的步骤视图；用例没有任何步骤与轮次时返回空数组。
 *
 * 分组口径（见 openspec/specs/agent-task-flow-report）：
 *   1. 步骤轴优先取 `cases[].steps`，缺失时按轮次的 `step_seq` 去重升序生成；
 *   2. 两者都没有时每个轮次各自成一步（存量数据退化）；
 *   3. 轮次一律按 `step_seq` 归入步骤、按角色分流，不依赖事件先后顺序。
 */
export function caseStepViews(
  caseItem: TaskReportCase | null | undefined,
  roundsById: Map<number, TaskReportRound>,
): StepView[] {
  const rounds = (caseItem?.round_ids || [])
    .map((roundId) => roundsById.get(roundId))
    .filter((round): round is TaskReportRound => Boolean(round))

  const bySeq = new Map<number, TaskReportRound[]>()
  for (const round of rounds) {
    const seq = Number(round?.step_seq)
    if (!(seq > 0)) continue
    const group = bySeq.get(seq)
    if (group) group.push(round)
    else bySeq.set(seq, [round])
  }

  const declared = normalizeSteps(caseItem?.steps)
  const steps: StepView[] = []
  const placed = new Set<number>()

  if (declared.length) {
    for (const step of declared) {
      const group = bySeq.get(step.seq) || []
      for (const round of group) placed.add(round.round_id)
      steps.push(buildStep(String(step.seq), step.seq, step, group))
    }
    appendOrphans(steps, rounds, placed)
    return steps
  }

  const seqs = [...bySeq.keys()].sort((a, b) => a - b)
  if (seqs.length) {
    for (const seq of seqs) {
      const group = bySeq.get(seq) || []
      for (const round of group) placed.add(round.round_id)
      const executor = group.find((round) => roundKind(round) === "executor")
      steps.push(buildStep(String(seq), seq, { action: executor?.subject || "" }, group))
    }
  }

  if (!rounds.length) return steps

  if (!seqs.length) {
    return rounds.map((round, index) =>
      buildStep(`r${round.round_id}`, index + 1, { action: round.subject || "" }, [round]),
    )
  }

  appendOrphans(steps, rounds, placed)
  return steps
}

/**
 * 事件时间取时分秒。
 *
 * Args:
 *   iso: 报告里的 ISO 时间串。
 *
 * Returns:
 *   `HH:mm:ss`；无法解析时返回空串，由调用方决定是否隐藏。
 */
export function formatClock(iso?: string): string {
  if (!iso) return ""
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ""
  return BEIJING_CLOCK.format(date)
}

/**
 * 毫秒转紧凑耗时文案。
 *
 * 口径：不足 1 分钟用 `42s`，不足 1 小时用 `3m12s`，超过 1 小时用 `1h02m`。
 *
 * Args:
 *   ms: 毫秒数，可空。
 *
 * Returns:
 *   紧凑文案；0、负数、非数字或不足 1 秒时返回空串（由调用方隐藏）。
 */
export function formatDurationMs(ms?: number | null): string {
  const total = Number(ms)
  if (!Number.isFinite(total) || total <= 0) return ""
  const seconds = Math.round(total / 1000)
  if (seconds < 1) return ""
  if (seconds < 60) return `${seconds}s`
  const pad = (value: number) => String(value).padStart(2, "0")
  const minutes = Math.floor(seconds / 60)
  const restSeconds = seconds % 60
  if (minutes < 60) return `${minutes}m${pad(restSeconds)}s`
  const hours = Math.floor(minutes / 60)
  return `${hours}h${pad(minutes % 60)}m`
}
