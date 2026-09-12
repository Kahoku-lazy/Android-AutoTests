/**
 * [P0] 必测 — 任务详情加载与运行中轮询
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as taskApi from '@/modules/ai-assistant/api/tasks'
import { useTaskDetail } from '@/modules/ai-assistant/composables/useTaskDetail'
import { mountComposable } from '../../helpers/mountComposable'
import type { TaskDetail } from '@/shared/types/ai'

vi.mock('@/modules/ai-assistant/api/tasks', () => ({
  getTask: vi.fn(),
}))

function makeDetail(status: string, summary: string): TaskDetail {
  return {
    id: 9,
    title: 't',
    goal: 'g',
    status,
    run: { status: status === 'running' ? 'running' : 'success', summary, plans: [] },
  }
}

describe('[P0] useTaskDetail', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('running 时定时刷新详情，终态后停止', async () => {
    vi.mocked(taskApi.getTask)
      .mockResolvedValueOnce({ status: true, data: makeDetail('running', '') })
      .mockResolvedValueOnce({ status: true, data: makeDetail('running', '已规划 2 个步骤') })
      .mockResolvedValueOnce({ status: true, data: makeDetail('completed', '完成') })

    const { result, wrapper } = await mountComposable(() => useTaskDetail())
    await result.load(9)
    await flushPromises()
    expect(result.detail.value?.status).toBe('running')
    expect(taskApi.getTask).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(result.detail.value?.run?.summary).toBe('已规划 2 个步骤')
    expect(taskApi.getTask).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(result.detail.value?.status).toBe('completed')
    expect(taskApi.getTask).toHaveBeenCalledTimes(3)

    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(taskApi.getTask).toHaveBeenCalledTimes(3)

    wrapper.unmount()
  })

  it('stop 后不再轮询', async () => {
    vi.mocked(taskApi.getTask).mockResolvedValue({
      status: true,
      data: makeDetail('running', ''),
    })

    const { result, wrapper } = await mountComposable(() => useTaskDetail())
    await result.load(9)
    await flushPromises()
    result.stop()

    await vi.advanceTimersByTimeAsync(6000)
    await flushPromises()
    expect(taskApi.getTask).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })
})
