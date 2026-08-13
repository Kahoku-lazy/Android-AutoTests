/**
 * [P0] 必测 — test-runner 任务变更防抖保存（fake timers，不真实等待 1s）
 * 目录：tests/test-runner/p0/
 *
 * useDebouncedSave：scheduleSave 只对脏任务在 1s 后调 save、同 id 连续调度去重只存一次、
 * flushSave 立即落盘并清定时器、任务已从 tasks 删除后 flush 不崩溃不调 save。
 * 全部依赖注入（tasks ref + saveTaskToServer vi.fn()），无需 vi.mock。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useDebouncedSave } from '@/modules/test-runner/composables/useDebouncedSave'

const SAVE_DEBOUNCE_MS = 1000

function makeTasks() {
  return ref([
    { id: 't1', name: '任务一', status: 'queued' },
    { id: 't2', name: '任务二', status: 'queued' },
  ])
}

describe('[P0] useDebouncedSave', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('推进 1s：只对脏任务调 save', async () => {
    const tasks = makeTasks()
    const saveTaskToServer = vi.fn()
    const { scheduleSave } = useDebouncedSave(tasks, saveTaskToServer)

    scheduleSave('t1')
    expect(saveTaskToServer).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(SAVE_DEBOUNCE_MS)
    expect(saveTaskToServer).toHaveBeenCalledTimes(1)
    expect(saveTaskToServer).toHaveBeenCalledWith(tasks.value[0])
    expect(saveTaskToServer).not.toHaveBeenCalledWith(tasks.value[1])
  })

  it('同 id 连续调度：去重只存一次', async () => {
    const tasks = makeTasks()
    const saveTaskToServer = vi.fn()
    const { scheduleSave } = useDebouncedSave(tasks, saveTaskToServer)

    scheduleSave('t1')
    scheduleSave('t1')

    await vi.advanceTimersByTimeAsync(SAVE_DEBOUNCE_MS)
    expect(saveTaskToServer).toHaveBeenCalledTimes(1)
    expect(saveTaskToServer).toHaveBeenCalledWith(tasks.value[0])
  })

  it('flushSave：立即保存并清定时器', async () => {
    const tasks = makeTasks()
    const saveTaskToServer = vi.fn()
    const { scheduleSave, flushSave } = useDebouncedSave(tasks, saveTaskToServer)

    scheduleSave('t1')
    flushSave()

    expect(saveTaskToServer).toHaveBeenCalledTimes(1)
    expect(saveTaskToServer).toHaveBeenCalledWith(tasks.value[0])

    await vi.advanceTimersByTimeAsync(SAVE_DEBOUNCE_MS)
    expect(saveTaskToServer).toHaveBeenCalledTimes(1)
  })

  it('任务已从 tasks 删除：不崩溃不调 save', async () => {
    const tasks = makeTasks()
    const saveTaskToServer = vi.fn()
    const { scheduleSave } = useDebouncedSave(tasks, saveTaskToServer)

    scheduleSave('t1')
    tasks.value = []

    await vi.advanceTimersByTimeAsync(SAVE_DEBOUNCE_MS)
    expect(saveTaskToServer).not.toHaveBeenCalled()
  })
})
