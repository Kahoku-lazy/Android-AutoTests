/**
 * [P0] 必测 — test-runner 任务操作编排（三分支/收敛/校验链，vi.mock 三模块）
 * 目录：tests/test-runner/p0/
 *
 * useTaskOperations：doStartTask 三分支（run_id 存在绑 WS / 设备忙入队 startQueuePolling /
 * 无 run 无 queue 设备不可用提示）、doStopTask stopRun 失败也收敛 done/stopped 并关闭 WS 保存、
 * doCancelQueue 404 视为成功继续重置、doRemoveTask 删除失败不剔除本地、
 * createAndStart 校验链 4 条（空名/无设备/无用例/间隔<5）各自短路且不调 startRun。
 * mock ../api + useTaskWebSocket + element-plus；15 个注入参数全 vi.fn()/ref（以源码为准）。
 * taskUtils 的 generateTaskId 写 localStorage，beforeEach clear() 防串扰。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as trApi from '@/modules/test-runner/api'
import { closeTaskWebSocket } from '@/modules/test-runner/composables/useTaskWebSocket'
import { useTaskOperations } from '@/modules/test-runner/composables/useTaskOperations'

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
    failedSteps: [],
    overallPass: 0, overallFail: 0,
    createdAt: '', creator: '',
    currentCaseTitle: '', currentIteration: 0, outcome: '', round: 0,
    ...overrides,
  }
}

function makeForm(overrides = {}) {
  return ref({
    name: '任务A', taskType: 'ui_automation', mode: 'case',
    deviceSerial: 'S1', caseIds: [1], loopCount: 1, intervalSeconds: 5,
    startAt: '', endAt: '',
    ...overrides,
  })
}

/** 按源码解构签名构造 15 个注入桩，全部返回以便逐项断言 */
function buildOps() {
  const tasks = ref([makeTask()])
  const cases = ref([{ id: 1, title: 'TC-1', steps_data: [] }])
  const devices = ref([])
  const availableCases = ref([])
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

describe('[P0] useTaskOperations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.mocked(trApi.startRun).mockResolvedValue({ data: { status: true, runs: [{ run_id: 'r1' }] } } as never)
    vi.mocked(trApi.stopRun).mockResolvedValue({ data: { status: true } } as never)
    vi.mocked(trApi.deleteTask).mockResolvedValue({ data: { status: true } } as never)
    vi.mocked(trApi.cancelQueue).mockResolvedValue({ data: { status: true } } as never)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── doStartTask 三分支 ──

  describe('doStartTask', () => {
    it('run_id 存在 → 更新任务状态并绑定 WS', async () => {
      const { ops, tasks, bindListTaskWS, taskAddLog, scheduleSave } = buildOps()

      await ops.doStartTask(tasks.value[0])

      const updated = tasks.value[0]
      expect(updated).toMatchObject({ running: true, runId: 'r1', status: 'running' })
      expect(bindListTaskWS).toHaveBeenCalledTimes(1)
      expect(bindListTaskWS).toHaveBeenCalledWith(updated, 'r1')
      expect(taskAddLog).toHaveBeenCalledWith(updated, '🚀 任务已启动')
      expect(scheduleSave).toHaveBeenCalledWith('t1')
    })

    it('设备忙入队 → 状态 queued 并启动队列轮询', async () => {
      const { ops, tasks, startQueuePolling, taskAddLog } = buildOps()
      vi.mocked(trApi.startRun).mockResolvedValue({ data: { status: true, queued: [{ client_task_id: 't1' }] } } as never)

      await ops.doStartTask(tasks.value[0])

      const task = tasks.value[0]
      expect(task).toMatchObject({ running: false, status: 'queued', outcome: '', conclusion: '' })
      expect(taskAddLog).toHaveBeenCalledWith(task, '⏳ 设备正忙，任务已加入队列等待执行')
      expect(ElMessage.info).toHaveBeenCalledWith('设备正忙，任务已加入队列，设备空闲后自动执行')
      expect(startQueuePolling).toHaveBeenCalledTimes(1)
    })

    it('无 run 无 queue → 设备不可用提示，任务回落未运行', async () => {
      const { ops, tasks, taskAddLog, scheduleSave } = buildOps()
      vi.mocked(trApi.startRun).mockResolvedValue({ data: { status: true } } as never)

      await ops.doStartTask(tasks.value[0])

      const task = tasks.value[0]
      expect(task.running).toBe(false)
      expect(taskAddLog).toHaveBeenCalledWith(task, '❌ 设备不可用，任务未启动', 'error')
      expect(ElMessage.warning).toHaveBeenCalledWith('设备不可用或未就绪，任务已保存，可在列表中重试')
      expect(ElMessage.error).not.toHaveBeenCalled()
      expect(scheduleSave).toHaveBeenCalledWith('t1')
    })
  })

  // ── doStopTask：失败也收敛 ──

  it('doStopTask：stopRun 失败也收敛 done/stopped 并关闭 WS 保存', async () => {
    const { ops, tasks, saveTaskToServer } = buildOps()
    const task = tasks.value[0]
    task.running = true
    task.runId = 'r1'
    vi.mocked(trApi.stopRun).mockRejectedValue(new Error('网络异常'))

    await ops.doStopTask(task)

    expect(task).toMatchObject({
      running: false, status: 'done', outcome: 'stopped',
      currentCaseTitle: '', currentIteration: 0,
    })
    expect(closeTaskWebSocket).toHaveBeenCalledWith('t1')
    expect(saveTaskToServer).toHaveBeenCalledWith(task)
    expect(ElMessage.error).toHaveBeenCalledWith('停止请求失败，请检查网络连接')
    expect(ElMessage.success).not.toHaveBeenCalled()
  })

  // ── doCancelQueue：404 视为成功 ──

  it('doCancelQueue：404 视为成功，继续重置任务状态', async () => {
    const { ops, tasks, saveTaskToServer } = buildOps()
    const task = tasks.value[0]
    task.running = true
    task.runId = 'r1'
    task.status = 'queued'
    task.caseItems = [{ id: 1 }]
    task.stepStates = [{ index: 0 }]
    task.overallPass = 5
    task.overallFail = 1
    task.failedSteps = [{ stepIndex: 1 }]
    task.logs = ['log1']
    vi.mocked(trApi.cancelQueue).mockRejectedValue({ response: { status: 404 } })

    await ops.doCancelQueue(task)

    expect(trApi.cancelQueue).toHaveBeenCalledWith('t1', 'S1')
    expect(task).toMatchObject({
      running: false, runId: '', status: 'idle',
      caseItems: [], stepStates: [], overallPass: 0, overallFail: 0,
      failedSteps: [], logs: [],
    })
    expect(saveTaskToServer).toHaveBeenCalledWith(task)
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  // ── doRemoveTask：失败不剔除 ──

  it('doRemoveTask：deleteTask 失败不剔除本地任务', async () => {
    const { ops, tasks } = buildOps()
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(trApi.deleteTask).mockRejectedValue(new Error('后端错误'))

    await ops.doRemoveTask(tasks.value[0])

    expect(tasks.value.some((t) => t.id === 't1')).toBe(true)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败，请检查网络后重试')
    expect(ElMessage.success).not.toHaveBeenCalled()
    expect(errSpy).toHaveBeenCalled()
  })

  // ── createAndStart 校验链 4 条 ──

  describe('createAndStart 校验链', () => {
    const showNewTask = ref(true)
    const resetNewForm = vi.fn()

    it('空任务名 → 提示且不调 startRun', async () => {
      const { ops } = buildOps()

      await ops.createAndStart(makeForm({ name: '   ' }), showNewTask, resetNewForm)

      expect(ElMessage.warning).toHaveBeenCalledWith('请输入任务名称')
      expect(trApi.startRun).not.toHaveBeenCalled()
    })

    it('UI 任务未选设备 → 提示且不调 startRun', async () => {
      const { ops } = buildOps()

      await ops.createAndStart(makeForm({ deviceSerial: '' }), showNewTask, resetNewForm)

      expect(ElMessage.warning).toHaveBeenCalledWith('Android UI 自动化任务需要选择执行设备')
      expect(trApi.startRun).not.toHaveBeenCalled()
    })

    it('未选用例 → 提示且不调 startRun', async () => {
      const { ops } = buildOps()

      await ops.createAndStart(makeForm({ caseIds: [] }), showNewTask, resetNewForm)

      expect(ElMessage.warning).toHaveBeenCalledWith('请至少选择一个测试用例')
      expect(trApi.startRun).not.toHaveBeenCalled()
    })

    it('轮间间隔小于 5 秒 → 提示且不调 startRun', async () => {
      const { ops } = buildOps()

      await ops.createAndStart(makeForm({ intervalSeconds: 3 }), showNewTask, resetNewForm)

      expect(ElMessage.warning).toHaveBeenCalledWith('轮间间隔最小为 5 秒，请重新设置')
      expect(trApi.startRun).not.toHaveBeenCalled()
    })
  })
})
