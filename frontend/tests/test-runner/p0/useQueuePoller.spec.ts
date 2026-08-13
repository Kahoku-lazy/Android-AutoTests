/**
 * [P0] 必测 — test-runner 排队任务轮询升级（fake timers，依赖注入，无 vi.mock）
 * 目录：tests/test-runner/p0/
 *
 * useQueuePoller：队列排空后轮询自动停止、client_task_id 匹配时任务升级 running
 * 并触发三个回调（onTaskActivated/taskAddLog/scheduleSave）、已 running 任务跳过、
 * getActiveRuns 抛错被吞不打断轮询、startQueuePolling 幂等不产生双定时器。
 * POLL_INTERVAL=1500；getActiveRuns 注入 mockResolvedValue 的 {data:{status,active}} 信封。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { useQueuePoller } from '@/modules/test-runner/composables/useQueuePoller'

const POLL_INTERVAL = 1500

function buildPoller(options: {
  tasks: ReturnType<typeof ref>
  getActiveRuns: ReturnType<typeof vi.fn>
}) {
  const isTaskQueued = vi.fn((t) => t.status === 'queued')
  const onTaskActivated = vi.fn()
  const taskAddLog = vi.fn()
  const scheduleSave = vi.fn()
  const poller = useQueuePoller(
    options.tasks,
    isTaskQueued,
    onTaskActivated,
    taskAddLog,
    scheduleSave,
    options.getActiveRuns,
  )
  return { poller, isTaskQueued, onTaskActivated, taskAddLog, scheduleSave }
}

describe('[P0] useQueuePoller', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('无排队任务：轮询自动停止', async () => {
    // 首轮匹配后任务升级 running，队列排空 → 轮询自动停止，不再请求后端
    const tasks = ref([{ id: 't1', status: 'queued', running: false }])
    const getActiveRuns = vi.fn().mockResolvedValue({
      data: { status: true, active: [{ client_task_id: 't1', run_id: 'R-1' }] },
    })
    const { poller } = buildPoller({ tasks, getActiveRuns })

    poller.startQueuePolling()
    await flushPromises()
    expect(getActiveRuns).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL)
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL)
    expect(getActiveRuns).toHaveBeenCalledTimes(1)
    expect(poller.queuePollTimer.value).toBeNull()
  })

  it('匹配 client_task_id：任务升级 running + 触发三个回调', async () => {
    const tasks = ref([{ id: 't1', status: 'queued', running: false }])
    const getActiveRuns = vi.fn().mockResolvedValue({
      data: { status: true, active: [{ client_task_id: 't1', run_id: 'R-9' }] },
    })
    const { poller, onTaskActivated, taskAddLog, scheduleSave } = buildPoller({
      tasks,
      getActiveRuns,
    })

    poller.startQueuePolling()
    await flushPromises()

    const updated = tasks.value[0]
    expect(updated).toMatchObject({ running: true, runId: 'R-9', status: 'running' })
    expect(onTaskActivated).toHaveBeenCalledTimes(1)
    expect(onTaskActivated).toHaveBeenCalledWith(updated, 'R-9')
    expect(taskAddLog).toHaveBeenCalledTimes(1)
    expect(taskAddLog).toHaveBeenCalledWith(updated, '🚀 排队任务已被后台调度，开始执行')
    expect(scheduleSave).toHaveBeenCalledTimes(1)
    expect(scheduleSave).toHaveBeenCalledWith('t1')
  })

  it('已 running 的任务：跳过', async () => {
    const tasks = ref([{ id: 't1', status: 'queued', running: true }])
    const getActiveRuns = vi.fn().mockResolvedValue({
      data: { status: true, active: [{ client_task_id: 't1', run_id: 'R-9' }] },
    })
    const { poller, onTaskActivated, taskAddLog, scheduleSave } = buildPoller({
      tasks,
      getActiveRuns,
    })

    poller.startQueuePolling()
    await flushPromises()

    expect(tasks.value[0].runId).toBeUndefined()
    expect(onTaskActivated).not.toHaveBeenCalled()
    expect(taskAddLog).not.toHaveBeenCalled()
    expect(scheduleSave).not.toHaveBeenCalled()
  })

  it('getActiveRuns 抛错：被吞不抛', async () => {
    const tasks = ref([{ id: 't1', status: 'queued', running: false }])
    const getActiveRuns = vi.fn().mockRejectedValue(new Error('后端不可用'))
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { poller } = buildPoller({ tasks, getActiveRuns })

    await expect(poller.pollQueuedTasks()).resolves.toBeUndefined()

    poller.startQueuePolling()
    await flushPromises()
    expect(getActiveRuns).toHaveBeenCalledTimes(2)
    expect(poller.queuePollTimer.value).not.toBeNull()

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL)
    expect(getActiveRuns).toHaveBeenCalledTimes(3)
    expect(errSpy).toHaveBeenCalled()
  })

  it('startQueuePolling：幂等不产生双定时器', async () => {
    const tasks = ref([{ id: 't1', status: 'queued', running: false }])
    // active 无匹配：任务保持排队，轮询持续 → 可观察每个 tick 的调用次数
    const getActiveRuns = vi.fn().mockResolvedValue({ data: { status: true, active: [] } })
    const { poller } = buildPoller({ tasks, getActiveRuns })

    poller.startQueuePolling()
    poller.startQueuePolling()
    await flushPromises()
    expect(getActiveRuns).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL)
    expect(getActiveRuns).toHaveBeenCalledTimes(2)
    expect(poller.queuePollTimer.value).not.toBeNull()
  })
})
