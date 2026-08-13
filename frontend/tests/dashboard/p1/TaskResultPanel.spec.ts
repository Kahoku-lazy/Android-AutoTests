/**
 * [P1] 建议测 — 任务执行结果面板（摘要 chip / 状态图标 / 任务跳转分支）
 * 目录：tests/dashboard/p1/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskResultPanel from '@/modules/dashboard/components/TaskResultPanel.vue'
import type { RecentTask } from '@/shared/types/dashboard'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const summary = { passed: 8, failed: 2, new_cases_week: 5 }

function mountPanel(props: { tasks?: RecentTask[]; summary?: typeof summary } = {}) {
  return mount(TaskResultPanel, {
    props: { summary, ...props },
  })
}

describe('[P1] TaskResultPanel', () => {
  beforeEach(() => {
    pushMock.mockClear()
  })

  it('摘要 chips 显示成功 / 失败 / 本周新建', () => {
    const wrapper = mountPanel()
    const text = wrapper.find('.task-result-panel__summary').text()
    expect(text).toContain('8')
    expect(text).toContain('成功')
    expect(text).toContain('2')
    expect(text).toContain('失败')
    expect(text).toContain('5')
    expect(text).toContain('本周新建')
  })

  it('任务为空：显示空态文案', () => {
    const wrapper = mountPanel({ tasks: [] })
    expect(wrapper.text()).toContain('暂无执行记录，前往执行引擎启动任务')
  })

  it('渲染任务标题、统计与时间', () => {
    const wrapper = mountPanel({
      tasks: [
        { id: 't1', status: 'partial', title: '回归冒烟', time: '10:00', passed: 9, failed: 1, total: 10 },
      ],
    })

    const row = wrapper.find('.task-row')
    expect(row.text()).toContain('回归冒烟')
    expect(row.text()).toContain('成功 9 · 失败 1 · 共 10 次')
    expect(row.text()).toContain('10:00')
  })

  it('状态映射：success 显示 ✓，未知状态回退 idle ○', () => {
    const wrapper = mountPanel({
      tasks: [
        { id: 'a', status: 'success', title: 'A' },
        { id: 'b', status: 'unknown-x', title: 'B' },
      ],
    })

    const statuses = wrapper.findAll('.task-row__status')
    expect(statuses[0].text()).toBe('✓')
    expect(statuses[0].classes()).toContain('is-success')
    expect(statuses[1].text()).toBe('○')
    expect(statuses[1].classes()).toContain('is-idle')
  })

  it('渲染任务内用例图标', () => {
    const wrapper = mountPanel({
      tasks: [
        {
          id: 't1',
          status: 'running',
          title: '任务',
          cases: [
            { title: 'c1', status: 'success' },
            { title: 'c2', status: 'failed' },
          ],
        },
      ],
    })

    expect(wrapper.findAll('.case-icon')).toHaveLength(2)
    expect(wrapper.find('.case-icon.is-failed').exists()).toBe(true)
  })

  it('running 任务点击：跳转任务详情页', async () => {
    const wrapper = mountPanel({
      tasks: [{ task_id: 'client-123', status: 'running', title: '执行中任务' }],
    })

    await wrapper.find('.task-row').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/runner/task/client-123')
  })

  it('已完成任务点击：跳转执行引擎列表页', async () => {
    const wrapper = mountPanel({
      tasks: [{ run_id: 'run-9', status: 'success', title: '已完成任务' }],
    })

    await wrapper.find('.task-row').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/runner')
  })

  it('无任何 ID 的任务：不可点击，点击不跳转', async () => {
    const wrapper = mountPanel({
      tasks: [{ status: 'idle', title: '孤立任务' }],
    })

    const row = wrapper.find('.task-row')
    expect(row.attributes('role')).toBeUndefined()

    await row.trigger('click')

    expect(pushMock).not.toHaveBeenCalled()
  })
})
