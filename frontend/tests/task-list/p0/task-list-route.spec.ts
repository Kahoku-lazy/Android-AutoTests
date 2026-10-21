/**
 * [P0] 任务清单路由 — /tasks 与 /tasks/:id 由独立模块提供，ai-assistant 不再挂任务页
 */
import { describe, expect, it } from 'vitest'
import aiRoutes from '@/modules/ai-assistant/routes'
import taskRoutes from '@/modules/task-list/routes'

describe('[P0] 任务清单路由', () => {
  it('/tasks 指向任务清单页', () => {
    const route = taskRoutes.find((item) => item.path === '/tasks')

    expect(route?.name).toBe('task-list')
    expect(route?.meta?.title).toBe('任务清单')
    expect(typeof route?.component).toBe('function')
  })

  it('/tasks/:id 指向任务详情页', () => {
    const route = taskRoutes.find((item) => item.path === '/tasks/:id')

    expect(route?.name).toBe('task-detail')
    expect(route?.meta?.title).toBe('任务详情')
    expect(typeof route?.component).toBe('function')
  })

  it('ai-assistant 不再挂任务页', () => {
    expect(aiRoutes.some((item) => item.path.startsWith('/tasks'))).toBe(false)
  })
})
