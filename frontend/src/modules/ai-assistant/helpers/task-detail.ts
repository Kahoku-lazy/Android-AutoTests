import type {
  TaskDetail,
  TaskRunLogEntry,
  TaskRunPlan,
  TaskRunRoleTrace,
  TaskRunStep,
  TaskRunExecutorOut,
  TaskRunToolTrace,
  TaskRunVerifierOut,
} from '@/shared/types/ai'

export type TaskStepPhase = 'pending' | 'running' | 'pass' | 'fail'

export interface TaskStepAttempt {
  loop: number
  executorResult: string
  executorMessage: string
  verifierResult: string
  actual: string
  /** 验收证据截图 URL（/media/...），无图为空 */
  screenshotUrl: string
  executorTrace: TaskRunRoleTrace
  verifierTrace: TaskRunRoleTrace
}

export interface TaskStepBlock {
  index: number
  action: string
  assert: string
  attempts: TaskStepAttempt[]
  passed: boolean
  phase: TaskStepPhase
}

const TERMINAL_STATUSES = new Set(['completed', 'success', 'failed', 'cancelled', 'paused'])

export function isTaskTerminal(status?: string): boolean {
  return TERMINAL_STATUSES.has((status || '').toLowerCase())
}

export function formatTaskTime(raw?: string): string {
  if (!raw) return ''
  return raw.replace('T', ' ').slice(0, 16)
}

export function formatTaskDuration(start?: string, end?: string): string {
  if (!start || !end) return '—'
  const ms = Date.parse(end.replace(' ', 'T')) - Date.parse(start.replace(' ', 'T'))
  if (!Number.isFinite(ms) || ms < 0) return '—'
  const sec = Math.round(ms / 1000)
  if (sec < 60) return `≈ ${sec}s`
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `≈ ${m}m ${s}s`
}

function normalizeResult(raw: unknown): string {
  if (typeof raw === 'boolean') return raw ? 'pass' : 'fail'
  if (typeof raw === 'string') {
    const s = raw.toLowerCase()
    if (s === 'pass' || s === 'true' || s === 'success') return 'pass'
    if (s === 'fail' || s === 'false' || s === 'failed') return 'fail'
    return s
  }
  return ''
}

function normalizeSteps(raw?: Array<string | TaskRunStep>): TaskRunStep[] {
  if (!raw?.length) return []
  return raw
    .map((s) => {
      if (typeof s === 'string') return { action: s, assert: '' }
      return {
        action: String(s?.action || '').trim(),
        assert: String(s?.assert || '').trim(),
      }
    })
    .filter((s) => s.action)
}

function executorOut(raw: TaskRunLogEntry['executor']): TaskRunExecutorOut {
  if (!raw) return {}
  if (typeof raw === 'string') return { message: raw, result: '' }
  return raw
}

function verifierOut(raw: TaskRunLogEntry['verifier']): TaskRunVerifierOut {
  return raw || {}
}

function toAttempt(entry: TaskRunLogEntry): TaskStepAttempt {
  const exec = executorOut(entry.executor)
  const ver = verifierOut(entry.verifier)
  return {
    loop: entry.loop,
    executorResult: normalizeResult(exec.result || entry.result),
    executorMessage: exec.message || (typeof entry.executor === 'string' ? entry.executor : '') || '',
    verifierResult: normalizeResult(ver.result),
    actual: ver.actual || ver.summary || '',
    screenshotUrl: attemptScreenshotUrl(entry.screenshot),
    executorTrace: entry.executor_trace || {},
    verifierTrace: entry.verifier_trace || {},
  }
}

export function hasRoleTrace(trace?: TaskRunRoleTrace): boolean {
  return Boolean(
    trace?.input
    || trace?.thinking?.length
    || trace?.tools?.length
    || trace?.text,
  )
}

export function toolTraceLine(tool: TaskRunToolTrace): string {
  const kind = tool.type === 'call' ? '调用' : tool.type === 'result' ? '返回' : tool.type === 'image' ? '截图' : (tool.type || '工具')
  const name = tool.name || (tool.media_type ? tool.media_type : '—')
  const bits = [kind, name]
  if (tool.input) bits.push(tool.input)
  if (tool.output) bits.push(tool.output)
  else if (tool.state) bits.push(tool.state)
  if (tool.screenshot_path) bits.push(tool.screenshot_path)
  return bits.join(' · ')
}

/** 工具行里可展示的截图 URL（仅 result 且带 screenshot_path） */
export function toolScreenshotUrl(tool: TaskRunToolTrace): string {
  if (tool.type !== 'result' && tool.type !== 'image') return ''
  return attemptScreenshotUrl(tool.screenshot_path)
}

export function attemptTraceSides(attempt: TaskStepAttempt): Array<{ key: string; label: string; trace: TaskRunRoleTrace }> {
  return [
    { key: 'exec', label: 'Executor Agent Info', trace: attempt.executorTrace },
    { key: 'ver', label: 'Verifier Agent Info', trace: attempt.verifierTrace },
  ].filter((side) => hasRoleTrace(side.trace))
}

/** MEDIA 相对路径 → 可展示 URL；旧任务无字段返回空 */
export function attemptScreenshotUrl(rel?: string): string {
  const path = (rel || '').trim()
  if (!path) return ''
  if (path.startsWith('http') || path.startsWith('data:') || path.startsWith('/')) return path
  return `/media/${path}`
}

function lastAttemptPassed(attempts: TaskStepAttempt[]): boolean {
  const last = attempts[attempts.length - 1]
  return last?.verifierResult === 'pass'
}

function logsForStep(logs: TaskRunLogEntry[], step: TaskRunStep, goal?: string): TaskRunLogEntry[] {
  const byAction = logs.filter((e) => e.action && e.action === step.action)
  if (byAction.length) return byAction
  // 旧协议：按 goal 挂日志
  if (goal) return logs.filter((e) => e.goal === goal)
  return []
}

/** 从 plans + log 聚合成逐步时间线（新协议一步一结果；旧协议兼容） */
export function taskStepBlocks(detail: TaskDetail | null): TaskStepBlock[] {
  const run = detail?.run || {}
  const logs = run.log || []
  const plans: TaskRunPlan[] = run.plans?.length ? run.plans : []
  const running = !isTaskTerminal(detail?.status)

  const steps: Array<TaskRunStep & { goal?: string }> = []
  if (plans.length) {
    for (const plan of plans) {
      const rawSteps = plan.steps || []
      const legacyStringSteps = rawSteps.length > 0 && rawSteps.every((s) => typeof s === 'string')
      const normalized = normalizeSteps(rawSteps)
      // 旧协议：steps 为字符串 + 目标级 verification / log.goal → 压成一步，避免日志挂到每一步
      if (legacyStringSteps || !normalized.length) {
        if (plan.goal) {
          steps.push({
            action: plan.goal,
            assert: plan.verification || '',
            goal: plan.goal,
          })
        }
      } else {
        for (const s of normalized) steps.push({ ...s, goal: plan.goal })
      }
    }
  } else {
    // 无 plans：从 log 去重 action / goal
    const seen = new Set<string>()
    for (const e of logs) {
      const key = e.action || e.goal || ''
      if (!key || seen.has(key)) continue
      seen.add(key)
      steps.push({ action: key, assert: e.assert || e.verification || '', goal: e.goal })
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
    if (passed) phase = 'pass'
    else if (running && i === firstOpen) phase = 'running'
    else if (running || !attempts.length) phase = 'pending'
    else phase = 'fail'
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
  return plan?.goal || detail?.goal || ''
}

export function stepBadgeText(block: TaskStepBlock, maxLoops: number): string {
  const last = block.attempts[block.attempts.length - 1]
  const loop = last?.loop
  if (block.phase === 'pass') {
    return loop != null ? `通过（重试 ${loop}/${maxLoops}）` : '通过'
  }
  if (block.phase === 'pending') return '待执行'
  if (block.phase === 'running') {
    return loop != null ? `执行中（重试 ${loop}/${maxLoops}）` : '执行中'
  }
  if (loop != null && loop >= maxLoops) {
    return `失败（重试 ${loop}/${maxLoops} 用尽）`
  }
  return loop != null ? `失败（重试 ${loop}/${maxLoops}）` : '失败'
}

export function stepTagClass(phase: TaskStepPhase): string {
  if (phase === 'pass') return 'td-tag--pass'
  if (phase === 'fail') return 'td-tag--fail'
  if (phase === 'running') return 'td-tag--run'
  return 'td-tag--wait'
}

export function taskPassCount(blocks: TaskStepBlock[]): string {
  if (!blocks.length) return '—'
  return `${blocks.filter((b) => b.passed).length} / ${blocks.length}`
}

export function currentStepLabel(blocks: TaskStepBlock[]): string {
  if (!blocks.length) return '—'
  const running = blocks.find((b) => b.phase === 'running')
  if (running) return `${running.index}/${blocks.length}`
  const pending = blocks.find((b) => b.phase === 'pending')
  if (pending) return `${pending.index}/${blocks.length}`
  return `${blocks.length}/${blocks.length}`
}

/** 默认选中：执行中 → 最后失败 → 最后一步 */
export function defaultStepIndex(blocks: TaskStepBlock[]): number {
  if (!blocks.length) return 0
  const running = blocks.findIndex((b) => b.phase === 'running')
  if (running >= 0) return running
  const fail = blocks.findIndex((b) => b.phase === 'fail')
  if (fail >= 0) return fail
  return blocks.length - 1
}
