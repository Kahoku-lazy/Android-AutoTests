/**
 * [P1] 建议测 — test-runner 任务操作类型分支与重启（vi.mock 三模块，与 P0 同惯例）
 * 目录：tests/test-runner/p1/
 *
 * useTaskOperations：initTaskProgress 用例来源类型分支（api_testing/web_automation 取
 * availableCases，ui_automation 取 cases——经 doStartTask 触发，用两源不同标题的用例
 * 断言 caseItems 出处与对应加载器调用）；restartTask 重置运行残留字段创建新任务
 * （round+1、新 ID、清 runId/日志/计数）后保存提示并自动启动（restartTask 不 await
 * doStartTask，vi.waitFor 等启动链路落地后再断言）；doRemoveTask running 带 runId
 * 先 stopRun + closeTaskWebSocket 再 deleteTask（含调用顺序断言）后本地剔除。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as trApi from '@/modules/test-runner/api'
import { useTaskOperations } from '@/modules/test-runner/composables/useTaskOperations'
import { closeTaskWebSocket } from '@/modules/test-runner/composables/useTaskWebSocket'

vi.mock('@/modules/test-runner/api', () => ({
  startRun: vi.fn(),
  stopRun: vi.fn(),
  deleteTask: vi.fn(),
  cancelQueue: vi.fn(),
}))
vi.mock('@/modules/test-runner/composables/useTaskWebSocket', () => ({
  closeTaskWebSocket: vi.fn(),
}))
vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn(), info: vi.fn() },
}))

function makeTask(overrides = {}) {
  return {
    id: 't1', name: '任务A', taskType: 'ui_automation', mode: 'case',
    deviceSerial: 'S1', caseIds: [1], loopCount: 1, intervalSeconds: 5,
    running: false, runId: '', status: 'idle',
    caseItems: [], stepStates: [], logs: [],
    overallPass: 0, overallFail: 0,
    createdAt: '', creator: '',
    currentCaseTitle: '', currentIteration: 0, outcome: '', round: 0,
    ...overrides,
  }
}

/**
 * 按源码解构签名构造 15 个注入桩。cases（TC-UI）与 availableCases（TC-API）
 * 同 id 不同内容，用于断言 initTaskProgress 的用例来源分支。
 */
function buildOps() {
  const tasks = ref([makeTask()])
  const cases = ref([
    { id: 1, title: 'TC-UI', steps_data: [{ type: 'click', xpath: '//ui', description: 'UI 步骤' }] },
  ])
  const devices = ref([])
  const availableCases = ref([
    { id: 1, title: 'TC-API', steps_data: [{ type: 'request', xpath: '', description: 'API 步骤' }] },
  ])
  const saveTaskToServer = vi.fn()
  const scheduleSave = vi.fn()
  const taskAddLog = vi.fn()
  const getCurrentUsername = vi.fn(() => 'tester')
  const bindListTaskWS = vi.fn()
  const loadCases = vi.fn()
  const loadApiCases = vi.fn()
  const loadWebCases = vi.fn()
  const loadDevices = vi.fn()
  const startQueuePolling = vi.fn()
  const activeTab = ref('waiting')
  const ops = useTaskOperations({
    tasks, cases, devices, availableCases,
    saveTaskToServer, scheduleSave, taskAddLog, getCurrentUsername,
    bindListTaskWS, loadCases, loadApiCases, loadWebCases,
    loadDevices, startQueuePolling, activeTab,
  })
  return {
    ops, tasks, cases, devices, availableCases,
    saveTaskToServer, scheduleSave, taskAddLog, getCurrentUsername,
    bindListTaskWS, loadCases, loadApiCases, loadWebCases,
    loadDevices, startQueuePolling, activeTab,
  }
}

describe('[P1] useTaskOperations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    trApi.startRun.mockResolvedValue({ data: { status: true, runs: [{ run_id: 'r1' }] } })
    trApi.stopRun.mockResolvedValue({ data: { status: true } })
    trApi.deleteTask.mockResolvedValue({ data: { status: true } })
    trApi.cancelQueue.mockResolvedValue({ data: { status: true } })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── initTaskProgress 用例来源类型分支 ──

  describe('initTaskProgress 用例来源类型分支', () => {
    it('api_testing 任务：caseItems 取自 availableCases 并调 loadApiCases', async () => {
      const ctx = buildOps()
      const task = makeTask({ taskType: 'api_testing' })
      ctx.tasks.value = [task]

      await ctx.ops.doStartTask(task)

      expect(ctx.loadApiCases).toHaveBeenCalledTimes(1)
      expect(ctx.loadWebCases).not.toHaveBeenCalled()
      expect(task.caseItems).toHaveLength(1)
      expect(task.caseItems[0]).toMatchObject({ id: 1, title: 'TC-API' })
      expect(task.caseItems[0].steps[0]).toMatchObject({ type: 'request', description: 'API 步骤' })
    })

    it('web_automation 任务：caseItems 取自 availableCases 并调 loadWebCases', async () => {
      const ctx = buildOps()
      const task = makeTask({ taskType: 'web_automation' })
      ctx.tasks.value = [task]

      await ctx.ops.doStartTask(task)

      expect(ctx.loadWebCases).toHaveBeenCalledTimes(1)
      expect(ctx.loadApiCases).not.toHaveBeenCalled()
      expect(task.caseItems).toHaveLength(1)
      expect(task.caseItems[0]).toMatchObject({ id: 1, title: 'TC-API' })
      expect(task.caseItems[0].steps[0]).toMatchObject({ type: 'request', description: 'API 步骤' })
    })

    it('ui_automation 任务：caseItems 取自 cases 且不调 api/web 加载器', async () => {
      const ctx = buildOps()
      const task = makeTask({ taskType: 'ui_automation' })
      ctx.tasks.value = [task]

      await ctx.ops.doStartTask(task)

      expect(ctx.loadCases).not.toHaveBeenCalled() // cases 非空短路加载
      expect(ctx.loadApiCases).not.toHaveBeenCalled()
      expect(ctx.loadWebCases).not.toHaveBeenCalled()
      expect(task.caseItems).toHaveLength(1)
      expect(task.caseItems[0]).toMatchObject({ id: 1, title: 'TC-UI' })
      expect(task.caseItems[0].steps[0]).toMatchObject({ type: 'click', xpath: '//ui', description: 'UI 步骤' })
    })
  })

  // ── restartTask：重置字段后重新启动 ──

  it('restartTask：重置运行残留字段建新任务、保存提示并自动启动', async () => {
    const ctx = buildOps()
    const orig = ctx.tasks.value[0]
    orig.round = 2
    orig.running = true
    orig.runId = 'R0'
    orig.status = 'running'
    orig.caseItems = [{ id: 1 }]
    orig.stepStates = [{ index: 0 }]
    orig.logs = ['log1']
    orig.overallPass = 9
    orig.overallFail = 9
    orig.currentCaseTitle = '旧用例'
    orig.currentIteration = 5
    orig.outcome = 'error'

    ctx.ops.restartTask(orig)

    // 同步断言：新任务推入且字段重置，旧任务不动
    expect(ctx.tasks.value).toHaveLength(2)
    const nt = ctx.tasks.value[1]
    expect(nt.id).not.toBe(orig.id)
    expect(nt.id).toMatch(/^ID-\d{3}$/)
    expect(nt).toMatchObject({
      name: '任务A', round: 3, mode: 'case', deviceSerial: 'S1',
      loopCount: 1, intervalSeconds: 5, caseIds: [1], creator: 'tester',
      running: false, runId: '', stepStates: [], logs: [],
      overallPass: 0, overallFail: 0,
      currentCaseTitle: '', currentIteration: 0, outcome: '',
    })
    expect(nt.caseItems).toHaveLength(1) // doStartTask 同步前缀已按 cases 映射
    expect(ctx.saveTaskToServer).toHaveBeenCalledWith(nt)
    expect(ElMessage.success).toHaveBeenCalledWith('已创建新任务「任务A」第3轮')
    expect(ctx.activeTab.value).toBe('incomplete') // taskBucket：未运行且无 outcome

    // restartTask 不 await doStartTask：等启动链路落地后断言
    await vi.waitFor(() => expect(ctx.bindListTaskWS).toHaveBeenCalledTimes(1))
    const started = ctx.tasks.value[1]
    expect(started).toMatchObject({ running: true, runId: 'r1', status: 'running' })
    expect(ctx.bindListTaskWS).toHaveBeenCalledWith(started, 'r1')
    expect(ctx.taskAddLog).toHaveBeenCalledWith(started, '🚀 任务已启动')
    expect(ctx.scheduleSave).toHaveBeenCalledWith(nt.id)
  })

  // ── doRemoveTask：running 带 runId 先停后删 ──

  it('doRemoveTask：running 带 runId 先 stopRun + closeTaskWebSocket 再 deleteTask，任务从本地剔除', async () => {
    const ctx = buildOps()
    const task = makeTask({ running: true, runId: 'r1' })
    ctx.tasks.value = [task]

    await ctx.ops.doRemoveTask(task)

    expect(trApi.stopRun).toHaveBeenCalledWith('r1')
    expect(closeTaskWebSocket).toHaveBeenCalledWith('t1')
    expect(trApi.deleteTask).toHaveBeenCalledWith('t1')
    expect(ctx.tasks.value).toHaveLength(0)
    expect(ElMessage.success).toHaveBeenCalledWith('已删除')
    // 「先停后删」顺序：stopRun 的调用序严格早于 deleteTask
    expect(vi.mocked(trApi.stopRun).mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(trApi.deleteTask).mock.invocationCallOrder[0],
    )
  })
})
