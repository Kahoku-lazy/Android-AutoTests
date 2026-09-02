/**
 * [P0] 必测 — 任务列表加载与按线路筛选
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
}))

function makeTask(id: number, route: TaskRecord['route']): TaskRecord {
  return {
    id,
    title: `task-${id}`,
    goal: `goal-${id}`,
    route,
    status: 'completed',
  }
}

describe('[P0] useTaskList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('load 成功后默认「全部任务」，切 Tab 只留下对应 route', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: {
        tasks: [
          makeTask(1, 'device_control'),
          makeTask(2, 'platform_task'),
          makeTask(3, 'device_control'),
        ],
      },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.tasks.value).toHaveLength(3)
    expect(result.activeFilter.value).toBe('all')
    expect(result.filteredItems.value).toHaveLength(3)

    result.activeFilter.value = 'platform_task'
    expect(result.filteredItems.value.map((t: TaskRecord) => t.id)).toEqual([2])

    result.activeFilter.value = 'device_control'
    expect(result.filteredItems.value.map((t: TaskRecord) => t.id)).toEqual([1, 3])

    wrapper.unmount()
  })

  it('列表为空时 emptyCopy 引导新建，不因切 Tab 改变', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    result.activeFilter.value = 'platform_task'
    expect(result.filteredItems.value).toHaveLength(0)
    expect(result.emptyCopy.value.text).toBe('还没有任务')
    expect(result.emptyCopy.value.hint).toContain('新建任务')

    wrapper.unmount()
  })

  it('仅有控制设备任务时，切到平台任务展示分类空态文案', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1, 'device_control')] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    result.activeFilter.value = 'platform_task'
    expect(result.filteredItems.value).toHaveLength(0)
    expect(result.emptyCopy.value.text).toBe('该分类下还没有任务')

    wrapper.unmount()
  })
})
