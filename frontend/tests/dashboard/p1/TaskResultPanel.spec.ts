/**
 * [P1] 任务执行结果面板 — 助手任务卡摘要 / 状态 / 跳转
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskResultPanel from '@/modules/dashboard/components/TaskResultPanel.vue'
import type { RecentTask } from '@/shared/types/dashboard'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const summary = { passed: 8, failed: 2 }

function mountPanel(props: { tasks?: RecentTask[]; summary?: typeof summary } = {}) {
  return mount(TaskResultPanel, {
    props: { summary, ...props },
  })
}

describe('[P1] TaskResultPanel', () => {
  beforeEach(() => {
    pushMock.mockClear()
  })

  it('摘要 chips：显示成功 / 失败', () => {
    const wrapper = mountPanel()
    const text = wrapper.find('.task-result-panel__summary').text()
    expect(text).toContain('8')
    expect(text).toContain('成功')
    expect(text).toContain('2')
    expect(text).toContain('失败')
  })

  it('任务为空：引导前往平台小助手', () => {
    const wrapper = mountPanel({ tasks: [] })
    expect(wrapper.text()).toContain('暂无任务卡片，前往平台小助手新建')
  })

  it('completed 映射为成功 ✓', () => {
    const wrapper = mountPanel({
      tasks: [{ id: 12, status: 'completed', title: '助手卡' }],
    })
    const status = wrapper.find('.task-row__status')
    expect(status.text()).toBe('✓')
    expect(status.classes()).toContain('is-success')
  })

  it('有 id 时点击进入助手任务详情', async () => {
    const wrapper = mountPanel({
      tasks: [{ id: 12, status: 'success', title: '已完成任务' }],
    })
    await wrapper.find('.task-row').trigger('click')
    expect(pushMock).toHaveBeenCalledWith('/ai-assistant/tasks/12')
  })

  it('无任何 ID 的任务：点击不跳转', async () => {
    const wrapper = mountPanel({
      tasks: [{ status: 'idle', title: '孤立任务' }],
    })
    await wrapper.find('.task-row').trigger('click')
    expect(pushMock).not.toHaveBeenCalled()
  })
})
