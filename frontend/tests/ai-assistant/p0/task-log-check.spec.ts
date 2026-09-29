/**
 * [P0] 必测 — 执行侧「日志检查」（spec: ai-executor-log-check / ai-task-publishing）
 *
 * 目录：tests/ai-assistant/p0/
 * 断言四件事：① 标记步骤给出时间点 + 截图路径 + 5 秒日志；
 * ② 未标记步骤只给时间点与截图、不出现日志内容；
 * ③ 无点击且无日志时不渲染该块；
 * ④ 与验收侧「设备日志证据」块并存，且点击后未截图时如实标注。
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskAttemptCard from '@/modules/ai-assistant/components/TaskAttemptCard.vue'
import {
  hasLogCheck,
  type TaskStepAttempt,
} from '@/modules/ai-assistant/helpers/task-detail'

const stubs = {
  'el-collapse': {
    template: '<div class="el-collapse"><slot /></div>',
  },
  'el-collapse-item': {
    props: ['title', 'name'],
    template:
      '<div class="el-collapse-item"><span>{{ title }}</span>'
      + '<div class="el-collapse-item__wrap" style="display:none"><slot /></div></div>',
  },
  'el-image': {
    props: ['src'],
    template: '<img class="el-image" :src="src" v-bind="$attrs" />',
  },
}

const CLICK_TIME = '2026-09-28 17:01:12.645'
const SHOT = 'ai_tasks/12/s2_l1.jpg'

const LOG = {
  conclusion: 'hit',
  window_line_count: 2,
  hits: [{ keyword: 'switch_off', grade: 'strong', count: 1 }],
}

function makeAttempt(overrides: Partial<TaskStepAttempt> = {}): TaskStepAttempt {
  return {
    loop: 1,
    executorResult: 'pass',
    executorMessage: '已点击开关',
    verifierResult: 'pass',
    actual: '日志命中',
    screenshotUrl: '/media/ai_tasks/12/s2_l1_verify.jpg',
    executorTrace: {},
    verifierTrace: {},
    ...overrides,
  }
}

function mountCard(overrides: Partial<TaskStepAttempt> = {}) {
  return mount(TaskAttemptCard, {
    props: { attempt: makeAttempt(overrides), maxLoops: 3 },
    global: { stubs },
  })
}

describe('[P0] 执行侧日志检查块', () => {
  it('标记步骤：时间点 + 截图路径 + 5 秒日志同块呈现', () => {
    const wrapper = mountCard({
      logCheck: {
        clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }],
        log: LOG,
      },
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain('日志检查')
    expect(block.text()).toContain(CLICK_TIME)
    expect(block.text()).toContain(SHOT)
    expect(block.find('[data-testid="step-log-evidence"]').exists()).toBe(true)
    expect(block.text()).toContain('switch_off')
  })

  it('截图可在块内查看（媒体路径经登记处拼接）', () => {
    const wrapper = mountCard({
      logCheck: { clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }], log: null },
    })
    const shot = wrapper.find('[data-testid="log-check-screenshot"]')
    expect(shot.exists()).toBe(true)
    expect(shot.attributes('src')).toBe(`/media/${SHOT}`)
  })

  it('未标记步骤：只给时间点与截图，不出现日志内容', () => {
    const wrapper = mountCard({
      logCheck: { clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }], log: null },
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.exists()).toBe(true)
    expect(block.text()).toContain(CLICK_TIME)
    expect(block.find('[data-testid="step-log-evidence"]').exists()).toBe(false)
  })

  it('点击后未截图时如实标注，不借用验收截图', () => {
    const wrapper = mountCard({
      logCheck: { clicks: [{ action_time: CLICK_TIME, screenshot_path: '' }], log: null },
    })
    const block = wrapper.find('[data-testid="step-log-check"]')
    expect(block.text()).toContain('该次点击后未截图')
    expect(block.find('[data-testid="log-check-screenshot"]').exists()).toBe(false)
  })

  it('一步多次点击各自成条', () => {
    const wrapper = mountCard({
      logCheck: {
        clicks: [
          { action_time: CLICK_TIME, screenshot_path: SHOT },
          { action_time: '2026-09-28 17:01:15.000', screenshot_path: 'ai_tasks/12/s2_l2.jpg' },
        ],
        log: null,
      },
    })
    const clicks = wrapper.findAll('.slc-click')
    expect(clicks.length).toBe(2)
    expect(clicks[1].text()).toContain('2026-09-28 17:01:15.000')
  })

  it('无点击且无日志时不渲染该块（不留空壳）', () => {
    expect(mountCard().find('[data-testid="step-log-check"]').exists()).toBe(false)
    expect(
      mountCard({ logCheck: { clicks: [], log: null } })
        .find('[data-testid="step-log-check"]')
        .exists(),
    ).toBe(false)
  })

  it('老任务（无该字段）不报错，验收证据块照常', () => {
    const wrapper = mountCard({ logEvidence: LOG })
    expect(wrapper.find('[data-testid="step-log-check"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="step-log-evidence"]').exists()).toBe(true)
  })

  it('执行侧检查块与验收侧证据块并存', () => {
    const wrapper = mountCard({
      logCheck: { clicks: [{ action_time: CLICK_TIME, screenshot_path: SHOT }], log: LOG },
      logEvidence: LOG,
    })
    expect(wrapper.find('[data-testid="step-log-check"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="step-log-evidence"]').exists()).toBe(true)
  })
})

describe('[P0] hasLogCheck', () => {
  it('只认「有点击」或「有日志」两种内容', () => {
    expect(hasLogCheck(undefined)).toBe(false)
    expect(hasLogCheck(null)).toBe(false)
    expect(hasLogCheck({})).toBe(false)
    expect(hasLogCheck({ clicks: [], log: null })).toBe(false)
    expect(hasLogCheck({ clicks: [{ action_time: CLICK_TIME }] })).toBe(true)
    expect(hasLogCheck({ clicks: [], log: LOG })).toBe(true)
  })
})
