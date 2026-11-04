/**
 * [P0] 必测 — 任务详情运行中自动刷新不打断阅读
 * 目录：tests/task-list/p0/
 *
 * 覆盖 spec「自动刷新不打断已读位置」「运行中给出可见的刷新信号」：
 * 用例集合不变时刷新不动展开态；新增用例才回到默认；新轮次追加在末尾；
 * 运行中显示标识与最后更新时间。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

const mocks = vi.hoisted(() => ({
  getTaskReport: vi.fn(),
  push: vi.fn(),
}))

vi.mock('@/modules/task-list/api/tasks', () => ({
  getTaskReport: mocks.getTaskReport,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ push: mocks.push }),
}))

import TaskDetailPage from '@/modules/task-list/TaskDetailPage.vue'

type ReportOptions = {
  caseTitles?: string[]
  extraRound?: boolean
  status?: string
}

/** 造一份报告：每条用例 2 步，每步一次执行 + 一次验收 */
function makeReport(options: ReportOptions = {}) {
  const caseTitles = options.caseTitles ?? ['用例甲', '用例乙']
  const rounds: Record<string, unknown>[] = []
  const cases: Record<string, unknown>[] = []
  let roundId = 0

  for (const title of caseTitles) {
    const roundIds: number[] = []
    for (const seq of [1, 2]) {
      rounds.push({
        round_id: roundId,
        role: 'executor_role',
        role_kind: 'executor',
        model: 'deepseek-flash',
        step_seq: seq,
        attempt: 1,
        subject: `${title}动作${seq}`,
        blocks: [],
        verdict: null,
      })
      roundIds.push(roundId)
      roundId += 1
      rounds.push({
        round_id: roundId,
        role: 'verifier_role',
        role_kind: 'verifier',
        model: 'deepseek-flash',
        step_seq: seq,
        attempt: 1,
        subject: `${title}动作${seq}`,
        blocks: [],
        verdict: { passed: true, message: '通过' },
      })
      roundIds.push(roundId)
      roundId += 1
    }
    cases.push({
      title,
      outcome: 'PASS',
      steps: [1, 2].map((seq) => ({
        seq,
        action: `${title}动作${seq}`,
        expected: `预期${seq}`,
        outcome: 'PASS',
      })),
      round_ids: roundIds,
    })
  }

  // 新轮次：第 1 条用例的第 1 步再跑一次（追加在最后）
  if (options.extraRound) {
    rounds.push({
      round_id: roundId,
      role: 'executor_role',
      role_kind: 'executor',
      model: 'deepseek-flash',
      step_seq: 1,
      attempt: 2,
      subject: `${caseTitles[0]}动作1`,
      blocks: [],
      verdict: null,
    })
    ;(cases[0].round_ids as number[]).push(roundId)
  }

  return {
    status: true,
    data: {
      task: { id: 1, title: '定时任务测试', status: options.status ?? 'running', cost_total: 0 },
      rounds,
      cases,
      conclusion: { outcome: 'PASS' },
    },
  }
}

/** 推进假时钟并让 Vue 完成渲染 */
async function settle(ms = 0) {
  await vi.advanceTimersByTimeAsync(ms)
  await nextTick()
  await nextTick()
}

async function mountPage(report: unknown): Promise<VueWrapper> {
  mocks.getTaskReport.mockResolvedValue(report)
  const wrapper = mount(TaskDetailPage)
  await settle(0)
  return wrapper
}

/** 下一次轮询返回新的报告 */
function nextReport(report: unknown) {
  mocks.getTaskReport.mockResolvedValue(report)
}

describe('[P0] 任务详情自动刷新不打断阅读', () => {
  let wrapper: VueWrapper | null = null

  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
    vi.useRealTimers()
  })

  it('用例集合不变时，展开的用例与步骤都保持展开', async () => {
    wrapper = await mountPage(makeReport())

    // 默认只展开第一个用例；再手动展开第二个用例的第 1 步
    await wrapper.findAll('.flow-case__title')[1].trigger('click')
    await wrapper.findAll('.flow-step__title')[0].trigger('click')
    expect(wrapper.findAll('.flow-case__body')).toHaveLength(2)
    expect(wrapper.findAll('.flow-step__body')).toHaveLength(1)

    for (let i = 0; i < 3; i += 1) {
      nextReport(makeReport())
      await settle(3000)
    }

    expect(mocks.getTaskReport).toHaveBeenCalledTimes(4)
    expect(wrapper.findAll('.flow-case__body')).toHaveLength(2)
    expect(wrapper.findAll('.flow-step__body')).toHaveLength(1)
  })

  it('出现新用例才回到默认展开', async () => {
    wrapper = await mountPage(makeReport())
    await wrapper.findAll('.flow-case__title')[1].trigger('click')
    expect(wrapper.findAll('.flow-case__body')).toHaveLength(2)

    nextReport(makeReport({ caseTitles: ['用例甲', '用例乙', '用例丙'] }))
    await settle(3000)

    const bodies = wrapper.findAll('.flow-case__body')
    expect(bodies).toHaveLength(1)
    expect(wrapper.findAll('.flow-case__title')[0].text()).toContain('用例甲')
  })

  it('新轮次追加在末尾，既有步骤顺序不变', async () => {
    wrapper = await mountPage(makeReport())
    const before = wrapper.findAll('.flow-step__text').map((node) => node.text())
    expect(before).toEqual(['1. 用例甲动作1', '2. 用例甲动作2'])

    nextReport(makeReport({ extraRound: true }))
    await settle(3000)

    const after = wrapper.findAll('.flow-step__text').map((node) => node.text())
    expect(after).toEqual(before)

    // 追加的尝试落在第 1 步的展开体里，成为「第2次」
    await wrapper.findAll('.flow-step__title')[0].trigger('click')
    const attemptTags = wrapper.findAll('.flow-attempt__tag').map((node) => node.text())
    expect(attemptTags).toEqual(['第1次', '第2次'])
  })

  it('运行中显示自动刷新标识与最后更新时间', async () => {
    wrapper = await mountPage(makeReport())
    expect(wrapper.find('.flow-live').text()).toContain('运行中')

    nextReport(makeReport())
    await settle(3000)
    expect(wrapper.text()).toContain('更新于')
  })

  it('任务进终态后不再刷新', async () => {
    wrapper = await mountPage(makeReport())
    expect(mocks.getTaskReport).toHaveBeenCalledTimes(1)

    nextReport(makeReport({ status: 'completed' }))
    await settle(3000)
    expect(mocks.getTaskReport).toHaveBeenCalledTimes(2)

    await settle(30000)
    expect(mocks.getTaskReport).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.flow-live').exists()).toBe(false)
  })
})
