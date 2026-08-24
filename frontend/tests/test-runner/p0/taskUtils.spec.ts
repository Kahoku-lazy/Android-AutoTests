/**
 * [P0] 必测 — test-runner 任务状态/进度/持久化共享逻辑
 * 目录：tests/test-runner/p0/
 *
 * taskUtils.ts：deriveTaskStatus 全分支、generateTaskId 计数器递增与跳过、
 * buildTaskSavePayload 截断与默认值、taskPassRate 除零、taskBucket 四分类。
 * 全局单例卫生：readTaskCounter/writeTaskCounter 读写 localStorage _task_id_counter，
 * 每个用例前 clear()。
 */
import { beforeEach, describe, expect, it } from 'vitest'
import {
  buildTaskSavePayload,
  deriveTaskStatus,
  generateTaskId,
  taskBucket,
  taskPassRate,
} from '@/modules/test-runner/composables/taskUtils'

const COUNTER_KEY = '_task_id_counter'

describe('[P0] taskUtils', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  // ── deriveTaskStatus：Step 6 权威状态读取（判定收敛到后端 display_state）──

  describe('deriveTaskStatus', () => {
    it.each([
      {
        name: 'state=running，返回 running',
        task: { state: 'running' },
        expected: 'running',
      },
      {
        name: 'state=queued，返回 queued',
        task: { state: 'queued' },
        expected: 'queued',
      },
      {
        name: 'state=done（含漂移已由后端修正），返回 done',
        task: { state: 'done', status: 'queued', outcome: 'completed' },
        expected: 'done',
      },
      {
        name: 'state=idle，返回 idle',
        task: { state: 'idle' },
        expected: 'idle',
      },
      {
        name: '无 state（旧缓存/本地行），回退 idle（字段读取非推导）',
        task: { running: true, status: 'running' },
        expected: 'idle',
      },
      {
        name: '空任务对象，默认返回 idle',
        task: {},
        expected: 'idle',
      },
    ])('$name', ({ task, expected }) => {
      expect(deriveTaskStatus(task)).toBe(expected)
    })
  })

  // ── generateTaskId 计数器 ──

  describe('generateTaskId', () => {
    it('generateTaskId：连续调用计数器递增，格式 ID-001/ID-002', () => {
      expect(generateTaskId()).toBe('ID-001')
      expect(generateTaskId()).toBe('ID-002')
      expect(localStorage.getItem(COUNTER_KEY)).toBe('2')
    })

    it('generateTaskId：existingIds 含 ID-002，跳过生成 ID-003', () => {
      generateTaskId() // 计数器 → 1，ID-001 已占用

      expect(generateTaskId(new Set(['ID-002']))).toBe('ID-003')
    })

    it('generateTaskId：existingIds 连续占位，逐个跳过到 ID-004', () => {
      expect(generateTaskId(new Set(['ID-001', 'ID-002', 'ID-003']))).toBe('ID-004')
    })
  })

  // ── buildTaskSavePayload 截断与默认值 ──

  describe('buildTaskSavePayload', () => {
    it('buildTaskSavePayload：logs 超 200 条，截断保留最后 200 条', () => {
      const logs = Array.from({ length: 250 }, (_, i) => `log-${i}`)
      const payload = buildTaskSavePayload({ logs })

      expect(payload.logs).toHaveLength(200)
      expect(payload.logs[0]).toBe('log-50')
      expect(payload.logs[199]).toBe('log-249')
    })

    it('buildTaskSavePayload：failedSteps 超 200 条，截断保留最后 200 条', () => {
      const failedSteps = Array.from({ length: 250 }, (_, i) => ({ step: i }))
      const payload = buildTaskSavePayload({ failedSteps })

      expect(payload.failedSteps).toHaveLength(200)
      expect(payload.failedSteps[0]).toEqual({ step: 50 })
      expect(payload.failedSteps[199]).toEqual({ step: 249 })
    })

    it('buildTaskSavePayload：缺省字段补默认值', () => {
      const payload = buildTaskSavePayload({ id: 1, name: 't1', mode: 'ui' })

      expect(payload.id).toBe(1)
      expect(payload.name).toBe('t1')
      expect(payload.mode).toBe('ui')
      expect(payload.taskType).toBe('ui_automation')
      expect(payload.currentCaseTitle).toBe('')
      expect(payload.currentIteration).toBe(0)
      expect(payload.logs).toEqual([])
      expect(payload.failedSteps).toEqual([])
      expect(payload.conclusion).toBe('')
      expect(payload.bugTicket).toBe('')
      expect(payload.outcome).toBe('')
      expect(payload.round).toBe(0)
      expect(payload.startAt).toBe('')
      expect(payload.endAt).toBe('')
    })

    it('buildTaskSavePayload：显式字段原样透传', () => {
      const task = {
        id: 7,
        name: '回归',
        mode: 'case',
        taskType: 'api_testing',
        deviceSerial: 'S9',
        caseIds: [1, 2],
        loopCount: 3,
        intervalSeconds: 60,
        caseItems: [{ pass: 1, fail: 0, total: 1 }],
        stepStates: { a: 1 },
        overallPass: 9,
        overallFail: 1,
        createdAt: '2026-08-13',
        creator: 'wenle',
        currentCaseTitle: 'TC-1',
        currentIteration: 2,
        conclusion: '通过',
        bugTicket: 'BUG-1',
        outcome: 'completed',
        round: 1,
        startAt: '10:00',
        endAt: '10:01',
      }
      const payload = buildTaskSavePayload(task)

      expect(payload).toEqual({ ...task, logs: [], failedSteps: [] })
    })
  })

  // ── taskPassRate 除零 ──

  describe('taskPassRate', () => {
    it('taskPassRate：无 caseItems（completed=0），返回 100', () => {
      expect(taskPassRate({})).toBe(100)
    })

    it('taskPassRate：caseItems 全零（completed=0），返回 100', () => {
      expect(taskPassRate({ caseItems: [{ pass: 0, fail: 0, total: 10 }] })).toBe(100)
    })

    it('taskPassRate：正常占比四舍五入', () => {
      expect(
        taskPassRate({ caseItems: [{ pass: 9, fail: 1, total: 10 }], overallPass: 9 }),
      ).toBe(90)
    })
  })

  // ── taskBucket 四分类（Step 6：基于权威 state + outcome）──

  describe('taskBucket', () => {
    it.each([
      {
        name: 'state=running，归入 running',
        task: { state: 'running' },
        expected: 'running',
      },
      {
        name: 'state=queued，归入 waiting',
        task: { state: 'queued' },
        expected: 'waiting',
      },
      {
        name: 'state=done 且 outcome=completed，归入 completed',
        task: { state: 'done', outcome: 'completed' },
        expected: 'completed',
      },
      {
        name: 'state=done 且 outcome=stopped，归入 incomplete',
        task: { state: 'done', outcome: 'stopped' },
        expected: 'incomplete',
      },
      {
        name: 'state=done 且 outcome=interrupted，归入 incomplete',
        task: { state: 'done', outcome: 'interrupted' },
        expected: 'incomplete',
      },
      {
        name: 'state=done 且 outcome=error，归入 incomplete',
        task: { state: 'done', outcome: 'error' },
        expected: 'incomplete',
      },
      {
        name: '无 state（idle），默认归入 incomplete（现状语义）',
        task: {},
        expected: 'incomplete',
      },
      {
        name: '漂移行（后端已下发 state=done + completed），归入 completed',
        task: { state: 'done', status: 'queued', outcome: 'completed' },
        expected: 'completed',
      },
    ])('$name', ({ task, expected }) => {
      expect(taskBucket(task)).toBe(expected)
    })
  })
})
