/**
 * [P0] 必测 — 任务详情页只对「本次打开的任务」发请求
 * 目录：tests/task-list/p0/
 *
 * 回归两件事：
 * 1. 离开详情页时 `route.params.id` 变成 undefined，不得因此打出 `/api/tasks/NaN/report/`；
 * 2. 从任务 A 切到任务 B 时，A 的 keep-alive 缓存实例不得去拉 B 的报告。
 *
 * 挂载结构照抄 `App.vue`：RouterView → KeepAlive → 以 `route.path` 作 key 的页面组件。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, KeepAlive } from 'vue'
import { createMemoryHistory, createRouter, RouterView, useRoute } from 'vue-router'
import * as taskApi from '@/modules/task-list/api/tasks'
import TaskDetailPage from '@/modules/task-list/TaskDetailPage.vue'

vi.mock('@/modules/task-list/api/tasks', () => ({
  getTaskReport: vi.fn(),
  getTask: vi.fn(),
  getTaskMedia: vi.fn(),
  createTaskMediaLink: vi.fn(),
  uploadTaskFile: vi.fn(),
  submitTask: vi.fn(),
  listTasks: vi.fn(),
  listDevices: vi.fn(),
  deleteTask: vi.fn(),
  cancelTask: vi.fn(),
  rerunTask: vi.fn(),
  clearTasks: vi.fn(),
}))

/** 终态报告：页面不会开启自动刷新，请求次数只反映「打开了几次详情」 */
function completedReport(id: number) {
  return {
    status: true,
    data: {
      task: {
        id,
        title: `task-${id}`,
        task_kind: 'sop',
        status: 'completed',
        device: '',
        assistant: '',
        started_at: null,
        finished_at: null,
        cost_total: '0.0000',
        result: '',
      },
      conclusion: null,
      rounds: [],
      cases: [],
      events: [],
    },
  }
}

const Host = defineComponent({
  name: 'AppLikeHost',
  setup() {
    const route = useRoute()
    return () =>
      h(RouterView, null, {
        default: ({ Component }: { Component: unknown }) =>
          h(KeepAlive, null, {
            default: () => h(Component as never, { key: route.path }),
          }),
      })
  },
})

async function mountAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/tasks',
        name: 'task-list',
        component: defineComponent({ setup: () => () => h('div') }),
      },
      { path: '/tasks/:id', name: 'task-detail', component: TaskDetailPage },
    ],
  })
  await router.push(path)
  await router.isReady()

  const wrapper = mount(Host, { global: { plugins: [router] } })
  await flushPromises()
  return { router, wrapper }
}

function requestedIds(): number[] {
  return vi.mocked(taskApi.getTaskReport).mock.calls.map((call) => call[0] as number)
}

describe('[P0] 任务详情的任务标识', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.getTaskReport).mockImplementation((id: number) =>
      Promise.resolve(completedReport(id) as never),
    )
  })

  it('离开详情页不发 NaN 请求', async () => {
    const { router, wrapper } = await mountAt('/tasks/195')
    expect(requestedIds()).toEqual([195])

    await router.push('/tasks')
    await flushPromises()

    expect(requestedIds().every((id) => Number.isFinite(id))).toBe(true)
    expect(requestedIds()).toEqual([195])

    wrapper.unmount()
  })

  it('切换到另一个任务时，原缓存实例不请求新任务', async () => {
    const { router, wrapper } = await mountAt('/tasks/195')
    expect(requestedIds()).toEqual([195])

    await router.push('/tasks/201')
    await flushPromises()
    // 只有新实例为 201 发一次；195 的缓存实例不得跟随全局路由再拉一次
    expect(requestedIds()).toEqual([195, 201])

    await router.push('/tasks/195')
    await flushPromises()
    expect(requestedIds()).toEqual([195, 201])

    wrapper.unmount()
  })
})
