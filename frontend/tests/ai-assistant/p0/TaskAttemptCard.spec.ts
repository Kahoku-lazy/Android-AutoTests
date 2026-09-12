/**
 * [P0] 必测 — 任务尝试卡片（执行结果常显 / 截图不折叠 / Agent 默认收起）
 * 目录：tests/ai-assistant/p0/
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskAttemptCard from '@/modules/ai-assistant/components/TaskAttemptCard.vue'
import type { TaskStepAttempt } from '@/modules/ai-assistant/helpers/task-detail'

const stubs = {
  'el-collapse': {
    template: '<div class="el-collapse" data-testid="agent-collapse"><slot /></div>',
  },
  'el-collapse-item': {
    props: ['title', 'name'],
    template:
      '<div class="el-collapse-item" :data-name="name">'
      + '<span class="el-collapse-item__title">{{ title }}</span>'
      + '<div class="el-collapse-item__wrap" style="display:none"><slot /></div>'
      + '</div>',
  },
  'el-image': {
    props: ['src'],
    template: '<img class="el-image" :src="src" v-bind="$attrs" />',
  },
}

function makeAttempt(overrides: Partial<TaskStepAttempt> = {}): TaskStepAttempt {
  return {
    loop: 1,
    executorResult: 'pass',
    executorMessage: '已点击按钮',
    verifierResult: 'pass',
    actual: '页面已跳转',
    screenshotUrl: '/media/shots/verify-1.png',
    executorTrace: {
      input: '执行：点击登录',
      thinking: ['先找登录按钮'],
      tools: [{ type: 'call', name: 'tap', input: '登录' }],
      text: '点击完成',
    },
    verifierTrace: {
      input: '验收：进入首页',
      thinking: ['检查标题'],
      text: '验收通过',
    },
    ...overrides,
  }
}

function mountCard(attempt?: Partial<TaskStepAttempt>, maxLoops = 3) {
  return mount(TaskAttemptCard, {
    props: {
      attempt: makeAttempt(attempt),
      maxLoops,
    },
    global: { stubs },
  })
}

describe('[P0] TaskAttemptCard', () => {
  it('执行结果常显：含执行/验收结论，且不在 collapse 内', () => {
    const wrapper = mountCard()
    const result = wrapper.find('[data-testid="attempt-result"]')
    expect(result.exists()).toBe(true)
    expect(result.text()).toContain('执行')
    expect(result.text()).toContain('pass')
    expect(result.text()).toContain('已点击按钮')
    expect(result.text()).toContain('验收')
    expect(result.text()).toContain('页面已跳转')
    expect(result.find('.el-collapse').exists()).toBe(false)
    expect(wrapper.find('[data-testid="agent-collapse"]').exists()).toBe(true)
  })

  it('有截图时 el-image 常显在结果区', () => {
    const wrapper = mountCard()
    const shot = wrapper.find('[data-testid="attempt-screenshot"]')
    expect(shot.exists()).toBe(true)
    expect(shot.attributes('src')).toBe('/media/shots/verify-1.png')
    const inResult = wrapper.find('[data-testid="attempt-result"] [data-testid="attempt-screenshot"]')
    expect(inResult.exists()).toBe(true)
  })

  it('Agent 折叠默认未展开', () => {
    const wrapper = mountCard()
    const collapse = wrapper.find('[data-testid="agent-collapse"]')
    expect(collapse.exists()).toBe(true)
    const wraps = collapse.findAll('.el-collapse-item__wrap')
    expect(wraps.length).toBeGreaterThan(0)
    wraps.forEach((w) => {
      const style = (w.attributes('style') || '').replace(/\s/g, '')
      expect(style).toContain('display:none')
    })
    expect(collapse.text()).toContain('Executor Agent Info')
    expect(collapse.text()).toContain('Verifier Agent Info')
  })

  it('标题与正文 class 分离', () => {
    const wrapper = mountCard()
    expect(wrapper.find('.tac__title').exists()).toBe(true)
    expect(wrapper.find('.tac-result__title').exists()).toBe(true)
    expect(wrapper.find('.tac-result__row').exists()).toBe(true)
    expect(wrapper.find('.tac-result__label').exists()).toBe(true)
  })
})
