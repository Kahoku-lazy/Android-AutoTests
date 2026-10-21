/**
 * [P0] 侧栏 AI任务 分组 — 任务清单入口与顺序
 */
import { describe, expect, it } from 'vitest'
import { NAV_CATEGORIES, MOD_COLORS } from '@/shared/components/sidebarNavConfig'

describe('[P0] 侧栏 AI任务 导航', () => {
  it('顺序为 任务清单 / 用例管理 / 测试报告', () => {
    const group = NAV_CATEGORIES.find((category) => category.key === 'ai-tasks')

    expect(group?.items.map((item) => item.label)).toEqual(['任务清单', '用例管理', '测试报告'])
    expect(group?.items.map((item) => item.path)).toEqual(['/tasks', '/cases', '/reports'])
  })

  it('任务清单有独立模块色，避免与 AI 助手共用高亮', () => {
    expect(MOD_COLORS['/tasks']).toBe('var(--c-ai)')
  })
})
