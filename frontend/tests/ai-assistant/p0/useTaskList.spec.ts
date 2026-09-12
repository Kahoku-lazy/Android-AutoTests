/**
 * [P0] 必测 — 任务列表加载、按状态分组、删除与清空
 * 目录：tests/ai-assistant/p0/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as taskApi from '@/modules/ai-assistant/api/tasks'
import { useTaskList } from '@/modules/ai-assistant/composables/useTaskList'
import { mountComposable } from '../../helpers/mountComposable'
import type { TaskRecord } from '@/shared/types/ai'

vi.mock('@/modules/ai-assistant/api/tasks', () => ({
  listTasks: vi.fn(),
  submitTask: vi.fn(),
  listDevices: vi.fn(),
  deleteTask: vi.fn(),
  clearTasks: vi.fn(),
}))

function makeTask(id: number): TaskRecord {
  return {
    id,
    title: `task-${id}`,
    goal: `goal-${id}`,
    status: 'completed',
  }
}

describe('[P0] useTaskList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('load 成功后默认「全部任务」', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2), makeTask(3)] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.tasks.value).toHaveLength(3)
    expect(result.activeFilter.value).toBe('all')
    expect(result.filteredItems.value).toHaveLength(3)

    wrapper.unmount()
  })

  it('列表为空时 emptyCopy 引导新建', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.filteredItems.value).toHaveLength(0)
    expect(result.emptyCopy.value.text).toBe('还没有任务')
    expect(result.emptyCopy.value.hint).toContain('新建任务')

    wrapper.unmount()
  })

  it('filteredItems 按状态分组合并 completed/success，空组不出现', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: {
        tasks: [
          { ...makeTask(1), status: 'pending' },
          { ...makeTask(2), status: 'completed' },
          { ...makeTask(3), status: 'success' },
          { ...makeTask(4), status: 'failed' },
        ],
      },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.groupedByStatus.value.map((g: { key: string }) => g.key)).toEqual([
      'pending', 'success', 'failed',
    ])
    const successGroup = result.groupedByStatus.value.find((g: { key: string }) => g.key === 'success')
    expect(successGroup?.items).toHaveLength(2)

    wrapper.unmount()
  })

  it('remove 成功后从列表去掉该任务', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2)] },
    })
    vi.mocked(taskApi.deleteTask).mockResolvedValue({ status: true })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    await result.remove(result.tasks.value[0])
    await flushPromises()

    expect(taskApi.deleteTask).toHaveBeenCalledWith(1)
    expect(result.tasks.value.map((t: TaskRecord) => t.id)).toEqual([2])

    wrapper.unmount()
  })

  it('clearAll 成功后列表为空', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2)] },
    })
    vi.mocked(taskApi.clearTasks).mockResolvedValue({ status: true, data: { deleted: 2 } })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    await result.clearAll()
    await flushPromises()

    expect(taskApi.clearTasks).toHaveBeenCalled()
    expect(result.tasks.value).toHaveLength(0)

    wrapper.unmount()
  })
})
