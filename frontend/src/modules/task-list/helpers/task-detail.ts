import type {
  TaskDetail,
  TaskLogCheck,
  TaskLogEvidence,
  TaskRunLogEntry,
  TaskRunPlan,
  TaskRunStep,
  TaskRunExecutorOut,
  TaskRunVerifierOut,
} from "@/shared/types/ai"
import { mediaUrl } from "@/shared/helpers/mediaUrl"

export type TaskStepPhase = "pending" | "running" | "pass" | "fail"

export interface TaskStepAttempt {
  loop: number
  executorResult: string
  executorMessage: string

  executorClickTimer?: string

  executorScreenshotPath?: string

  executorScreenshotUrl?: string
  verifierResult: string

  verifierLogTimer?: string

  verifierLogInfo?: string

  verifierScreenshotPath?: string
  actual: string

  screenshotUrl: string

  logEvidence?: TaskLogEvidence

  logCheck?: TaskLogCheck
}

export interface TaskStepBlock {
  index: number
  action: string
  assert: string
  attempts: TaskStepAttempt[]
  passed: boolean
  phase: TaskStepPhase
}

const TERMINAL_STATUSES = new Set([
  "completed",
  "success",
  "failed",
  "cancelled",
  "paused",
  "interrupted",
])

export function isTaskTerminal(status?: string): boolean {
  return TERMINAL_STATUSES.has((status || "").toLowerCase())
}

export function formatTaskTime(raw?: string): string {
  if (!raw) return ""
  return raw.replace("T", " ").slice(0, 16)
}

export function formatTaskDuration(start?: string, end?: string): string {
  if (!start || !end) return "—"
  const ms = Date.parse(end.replace(" ", "T")) - Date.parse(start.replace(" ", "T"))
  if (!Number.isFinite(ms) || ms < 0) return "—"
  const sec = Math.round(ms / 1000)
  if (sec < 60) return `≈ ${sec}s`
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `≈ ${m}m ${s}s`
}

export function formatTaskCost(cost?: number): string {
  return `${Number(cost ?? 0).toFixed(4)} 元`
}

const JSON_BLOCK_INDENT = "  "

const JSON_ESCAPE_TABLE: Record<string, string> = {
  "\\": "\\\\",
  '"': '\\"',
  "\b": "\\b",
  "\f": "\\f",
  "\t": "\\t",
}

function lineBreakText(whole: string, index: number, pad: string): string {
  const next = whole[index + 1]
  return next === undefined || next === "\n" || next === "\r" ? "\n" : `\n${pad}`
}

function escapeOtherChar(ch: string): string {
  const code = ch.charCodeAt(0)
  return code < 0x20 ? `\\u${code.toString(16).padStart(4, "0")}` : ch
}

function renderJsonString(value: string, depth: number): string {
  const pad = JSON_BLOCK_INDENT.repeat(depth)
  let body = ""
  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i]
    if (ch === "\n") {
      body += lineBreakText(value, i, pad)
      continue
    }

    if (ch === "\r") {
      if (value[i + 1] !== "\n") body += lineBreakText(value, i, pad)
      continue
    }
    body += JSON_ESCAPE_TABLE[ch] ?? escapeOtherChar(ch)
  }
  return `"${body}"`
}

function renderJsonValue(value: unknown, depth: number): string {
  const pad = JSON_BLOCK_INDENT.repeat(depth)
  if (value === null || value === undefined) return "null"
  if (typeof value === "string") return renderJsonString(value, depth)
  if (typeof value === "number" || typeof value === "boolean") return JSON.stringify(value)
  if (Array.isArray(value)) {
    if (!value.length) return "[]"
    const items = value.map((item) => pad + JSON_BLOCK_INDENT + renderJsonValue(item, depth + 1))
    return `[\n${items.join(",\n")}\n${pad}]`
  }
  const entries = Object.entries(value as Record<string, unknown>)
  if (!entries.length) return "{}"
  const lines = entries.map(
    ([key, item]) =>
      pad + JSON_BLOCK_INDENT + `${JSON.stringify(key)}: ${renderJsonValue(item, depth + 1)}`,
  )
  return `{\n${lines.join(",\n")}\n${pad}}`
}

export function formatPlannerInputText(raw?: string): string {
  const text = (raw ?? "").trim()
  if (!text) return ""
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    return text
  }
  return renderJsonValue(parsed, 0)
}

function normalizeResult(raw: unknown): string {
  if (typeof raw === "boolean") return raw ? "pass" : "fail"
  if (typeof raw === "string") {
    const s = raw.toLowerCase()
    if (s === "pass" || s === "true" || s === "success") return "pass"
    if (s === "fail" || s === "false" || s === "failed") return "fail"
    return s
  }
  return ""
}

function normalizeSteps(raw?: Array<string | TaskRunStep>): TaskRunStep[] {
  if (!raw?.length) return []
  return raw
    .map((s) => {
      if (typeof s === "string") return { action: s, assert: "" }
      return {
        action: String(s?.action || "").trim(),
        assert: String(s?.assert || "").trim(),
      }
    })
    .filter((s) => s.action)
}

function executorOut(raw: TaskRunLogEntry["executor"]): TaskRunExecutorOut {
  if (!raw) return {}
  if (typeof raw === "string") return { message: raw, result: "" }
  return raw
}

function verifierOut(raw: TaskRunLogEntry["verifier"]): TaskRunVerifierOut {
  return raw || {}
}

function toAttempt(entry: TaskRunLogEntry): TaskStepAttempt {
  const exec = executorOut(entry.executor)
  const ver = verifierOut(entry.verifier)
  const execShot = String(exec.screenshot || "").trim()
  return {
    loop: entry.loop,
    executorResult: normalizeResult(exec.result || entry.result),
    executorMessage:
      exec.message || (typeof entry.executor === "string" ? entry.executor : "") || "",
    executorClickTimer: String(exec.click_timer || "").trim(),
    executorScreenshotPath: execShot,
    executorScreenshotUrl: attemptScreenshotUrl(execShot),
    verifierResult: normalizeResult(ver.result),
    verifierLogTimer: String(ver.logAssertionTimer || "").trim(),
    verifierLogInfo: String(ver.logAssertionInfo || "").trim(),
    verifierScreenshotPath: String(ver.screenshot || "").trim(),
    actual: ver.actual || ver.summary || "",
    screenshotUrl: attemptScreenshotUrl(entry.screenshot),
    logEvidence: entry.log_evidence,
    logCheck: entry.executor_log_check,
  }
}

export function attemptScreenshotUrl(rel?: string): string {
  const path = (rel || "").trim()
  if (!path) return ""
  if (path.startsWith("http") || path.startsWith("data:") || path.startsWith("/")) return path
  return mediaUrl(path)
}

export function hasLogCheck(check?: TaskLogCheck | null): boolean {
  if (!check) return false
  return Boolean(check.clicks?.length) || Boolean(check.log)
}

function lastAttemptPassed(attempts: TaskStepAttempt[]): boolean {
  const last = attempts[attempts.length - 1]
  return last?.verifierResult === "pass"
}

function logsForStep(logs: TaskRunLogEntry[], step: TaskRunStep, goal?: string): TaskRunLogEntry[] {
  const byAction = logs.filter((e) => e.action && e.action === step.action)
  if (byAction.length) return byAction

  if (goal) return logs.filter((e) => e.goal === goal)
  return []
}

export function taskStepBlocks(detail: TaskDetail | null): TaskStepBlock[] {
  const run = detail?.run || {}
  const logs = run.log || []
  const plans: TaskRunPlan[] = run.plans?.length ? run.plans : []
  const running = !isTaskTerminal(detail?.status)

  const steps: Array<TaskRunStep & { goal?: string }> = []
  if (plans.length) {
    for (const plan of plans) {
      const rawSteps = plan.steps || []
      const legacyStringSteps = rawSteps.length > 0 && rawSteps.every((s) => typeof s === "string")
      const normalized = normalizeSteps(rawSteps)

      if (legacyStringSteps || !normalized.length) {
        if (plan.goal) {
          steps.push({
            action: plan.goal,
            assert: plan.verification || "",
            goal: plan.goal,
          })
        }
      } else {
        for (const s of normalized) steps.push({ ...s, goal: plan.goal })
      }
    }
  } else {
    const seen = new Set<string>()
    for (const e of logs) {
      const key = e.action || e.goal || ""
      if (!key || seen.has(key)) continue
      seen.add(key)
      steps.push({ action: key, assert: e.assert || e.verification || "", goal: e.goal })
    }
  }

  if (!steps.length) return []

  const firstOpen = steps.findIndex((step) => {
    const attempts = logsForStep(logs, step, step.goal).map(toAttempt)
    return !lastAttemptPassed(attempts)
  })

  return steps.map((step, i) => {
    const attempts = logsForStep(logs, step, step.goal).map(toAttempt)
    const passed = lastAttemptPassed(attempts)
    let phase: TaskStepPhase
    if (passed) phase = "pass"
    else if (running && i === firstOpen) phase = "running"
    else if (running || !attempts.length) phase = "pending"
    else phase = "fail"
    return {
      index: i + 1,
      action: step.action,
      assert: step.assert,
      attempts,
      passed,
      phase,
    }
  })
}

export function planGoalText(detail: TaskDetail | null): string {
  const plan = detail?.run?.plans?.[0]
  return plan?.goal || detail?.goal || ""
}

export function stepBadgeText(block: TaskStepBlock, maxLoops: number): string {
  const last = block.attempts[block.attempts.length - 1]
  const loop = last?.loop
  if (block.phase === "pass") {
    return loop != null ? `通过（重试 ${loop}/${maxLoops}）` : "通过"
  }
  if (block.phase === "pending") return "待执行"
  if (block.phase === "running") {
    return loop != null ? `执行中（重试 ${loop}/${maxLoops}）` : "执行中"
  }
  if (loop != null && loop >= maxLoops) {
    return `失败（重试 ${loop}/${maxLoops} 用尽）`
  }
  return loop != null ? `失败（重试 ${loop}/${maxLoops}）` : "失败"
}

export function stepTagClass(phase: TaskStepPhase): string {
  if (phase === "pass") return "td-tag--pass"
  if (phase === "fail") return "td-tag--fail"
  if (phase === "running") return "td-tag--run"
  return "td-tag--wait"
}

export function taskPassCount(blocks: TaskStepBlock[]): string {
  if (!blocks.length) return "—"
  return `${blocks.filter((b) => b.passed).length} / ${blocks.length}`
}

export function currentStepLabel(blocks: TaskStepBlock[]): string {
  if (!blocks.length) return "—"
  const running = blocks.find((b) => b.phase === "running")
  if (running) return `${running.index}/${blocks.length}`
  const pending = blocks.find((b) => b.phase === "pending")
  if (pending) return `${pending.index}/${blocks.length}`
  return `${blocks.length}/${blocks.length}`
}

export function defaultStepIndex(blocks: TaskStepBlock[]): number {
  if (!blocks.length) return 0
  const running = blocks.findIndex((b) => b.phase === "running")
  if (running >= 0) return running
  const fail = blocks.findIndex((b) => b.phase === "fail")
  if (fail >= 0) return fail
  return blocks.length - 1
}
