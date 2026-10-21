/**
 * [P0] 任务清单路由 — /tasks 独立于 /ai-assistant，避免侧栏双高亮
 */
import { describe, expect, it } from 'vitest'
import aiRoutes from '@/modules/ai-assistant/routes'

describe('[P0] 任务清单路由', () => {
  it('/tasks 指向任务清单页', () => {
    const route = aiRoutes.find((item) => item.path === '/tasks')

    expect(route?.name).toBe('ai-task-list')
    expect(route?.meta?.title).toBe('任务清单')
    expect(typeof route?.component).toBe('function')
  })

  it('任务清单路径不落在 /ai-assistant 前缀下', () => {
    const route = aiRoutes.find((item) => item.name === 'ai-task-list')

    expect(route?.path).toBe('/tasks')
    expect(route?.path.startsWith('/ai-assistant')).toBe(false)
  })
})
