import { describe, expect, it } from 'vitest'
import {
  currentStepLabel,
  defaultStepIndex,
  stepBadgeText,
  taskPassCount,
  taskStepBlocks,
} from '@/modules/ai-assistant/helpers/task-detail'
import type { TaskDetail } from '@/shared/types/ai'

describe('taskStepBlocks', () => {
  it('按 steps[{action,assert}] 聚合，验收 true 记为通过', () => {
    const detail: TaskDetail = {
      id: 1,
      title: 't',
      goal: '打开 govee',
      status: 'completed',
      run: {
        plans: [{
          goal: '打开 govee 并进入列表',
          steps: [
            { action: '启动 govee', assert: '前台为 govee' },
            { action: '点击设备 Tab', assert: '出现设备列表' },
          ],
        }],
        log: [
          {
            action: '启动 govee',
            assert: '前台为 govee',
            loop: 1,
            executor: { action: '启动 govee', result: 'PASS', message: '已启动' },
            verifier: {
              action: '启动 govee', assert: '前台为 govee', actual: '已在前台', result: true,
            },
          },
          {
            action: '点击设备 Tab',
            assert: '出现设备列表',
            loop: 1,
            executor: { action: '点击设备 Tab', result: 'FAIL', message: '未点到' },
            verifier: {
              action: '点击设备 Tab', assert: '出现设备列表', actual: '仍在首页', result: false,
            },
          },
        ],
      },
    }
    const blocks = taskStepBlocks(detail)
    expect(blocks).toHaveLength(2)
    expect(blocks[0].passed).toBe(true)
    expect(blocks[0].phase).toBe('pass')
    expect(blocks[1].passed).toBe(false)
    expect(blocks[1].phase).toBe('fail')
    expect(taskPassCount(blocks)).toBe('1 / 2')
  })

  it('同一步多轮重试保留 attempts，失败徽章标用尽', () => {
    const detail: TaskDetail = {
      id: 2,
      title: 't',
      goal: '启动',
      status: 'completed',
      run: {
        plans: [{
          goal: '启动',
          steps: [{ action: '启动应用', assert: '包名正确' }],
        }],
        log: [
          {
            action: '启动应用', assert: '包名正确', loop: 1,
            executor: { result: 'FAIL', message: '未就绪' },
            verifier: { result: false, actual: '未通过' },
          },
          {
            action: '启动应用', assert: '包名正确', loop: 2,
            executor: { result: 'PASS', message: '已启动' },
            verifier: { result: true, actual: 'ok' },
          },
        ],
      },
    }
    const blocks = taskStepBlocks(detail)
    expect(blocks[0].attempts).toHaveLength(2)
    expect(blocks[0].attempts[0].verifierResult).toBe('fail')
    expect(blocks[0].attempts[1].verifierResult).toBe('pass')
    expect(stepBadgeText(blocks[0], 3)).toBe('通过（重试 2/3）')

    blocks[0].passed = false
    blocks[0].phase = 'fail'
    blocks[0].attempts = [
      {
        loop: 3,
        executorResult: 'fail',
        executorMessage: '',
        verifierResult: 'fail',
        actual: 'x',
        screenshotUrl: '',
        executorTrace: {},
        verifierTrace: {},
      },
    ]
    expect(stepBadgeText(blocks[0], 3)).toBe('失败（重试 3/3 用尽）')
  })

  it('每轮验收截图映射为 /media URL', () => {
    const detail: TaskDetail = {
      id: 5,
      title: 't',
      goal: '启动',
      status: 'completed',
      run: {
        plans: [{
          goal: '启动',
          steps: [{ action: '启动应用', assert: '包名正确' }],
        }],
        log: [
          {
            action: '启动应用',
            assert: '包名正确',
            loop: 1,
            executor: { result: 'FAIL', message: '未就绪' },
            verifier: { result: false, actual: '未通过' },
            screenshot: 'ai_tasks/5/s1_l1.jpg',
          },
          {
            action: '启动应用',
            assert: '包名正确',
            loop: 2,
            executor: { result: 'PASS', message: '已启动' },
            verifier: { result: true, actual: 'ok' },
            screenshot: 'ai_tasks/5/s1_l2.jpg',
          },
        ],
      },
    }
    const blocks = taskStepBlocks(detail)
    expect(blocks[0].attempts[0].screenshotUrl).toBe('/media/ai_tasks/5/s1_l1.jpg')
    expect(blocks[0].attempts[1].screenshotUrl).toBe('/media/ai_tasks/5/s1_l2.jpg')
  })

  it('每轮映射执行/验收思考与工具调用', () => {
    const detail: TaskDetail = {
      id: 6,
      title: 't',
      goal: '启动',
      status: 'completed',
      run: {
        plans: [{
          goal: '启动',
          steps: [{ action: '启动应用', assert: '包名正确' }],
        }],
        log: [{
          action: '启动应用',
          assert: '包名正确',
          loop: 1,
          executor: { result: 'FAIL', message: '连接失败' },
          verifier: { result: false, actual: '未启动' },
          executor_trace: {
            input: '请执行：启动应用',
            thinking: ['设备看起来在线，先查 list_devices'],
            tools: [
              { type: 'call', name: 'list_devices', input: '{}' },
              { type: 'result', name: 'list_devices', state: 'done', output: '{"count":1}' },
            ],
            text: '{"result":"FAIL"}',
          },
          verifier_trace: {
            thinking: ['无法确认前台包名'],
            tools: [{
              type: 'result',
              name: 'screenshot_page',
              input: '{"serial":"x"}',
              screenshot_path: 'inspector/shots/capture_x.png',
              output: '{"screenshot_path":"inspector/shots/capture_x.png"}',
            }],
          },
        }],
      },
    }
    const blocks = taskStepBlocks(detail)
    const a = blocks[0].attempts[0]
    expect(a.executorTrace.input).toContain('启动应用')
    expect(a.executorTrace.thinking?.[0]).toContain('list_devices')
    expect(a.executorTrace.tools).toHaveLength(2)
    expect(a.executorTrace.text).toContain('FAIL')
    expect(a.verifierTrace.tools?.[0].name).toBe('screenshot_page')
    expect(a.verifierTrace.tools?.[0].screenshot_path).toBe('inspector/shots/capture_x.png')
  })

  it('运行中：首个未通过步骤为执行中，后续待执行', () => {
    const detail: TaskDetail = {
      id: 3,
      title: 't',
      goal: '主页跳转',
      status: 'running',
      run: {
        plans: [{
          goal: '跳转',
          steps: [
            { action: '点设备', assert: '设备页' },
            { action: '点生态', assert: '生态页' },
          ],
        }],
        log: [],
      },
    }
    const blocks = taskStepBlocks(detail)
    expect(blocks[0].phase).toBe('running')
    expect(blocks[1].phase).toBe('pending')
    expect(stepBadgeText(blocks[0], 3)).toBe('执行中')
    expect(stepBadgeText(blocks[1], 3)).toBe('待执行')
    expect(currentStepLabel(blocks)).toBe('1/2')
    expect(defaultStepIndex(blocks)).toBe(0)
  })

  it('旧协议：字符串 steps + goal 级 log 折叠成一步', () => {
    const detail: TaskDetail = {
      id: 4,
      title: 't',
      goal: '打开',
      status: 'completed',
      run: {
        plans: [{
          goal: '启动',
          steps: ['检查包名', '启动应用'],
          verification: '前台包名正确',
        }],
        log: [{
          goal: '启动',
          loop: 1,
          executor: '已启动',
          verifier: { result: 'pass', summary: 'ok' },
        }],
      },
    }
    const blocks = taskStepBlocks(detail)
    expect(blocks).toHaveLength(1)
    expect(blocks[0].action).toBe('启动')
    expect(blocks[0].assert).toBe('前台包名正确')
    expect(blocks[0].phase).toBe('pass')
  })
})
