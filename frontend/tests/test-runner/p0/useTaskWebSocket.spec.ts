/**
 * [P0] 必测 — test-runner WS 消息分发与断线重连（FakeWebSocket 桩 + fake timers，mock ws-url/token）
 * 目录：tests/test-runner/p0/
 *
 * useTaskWebSocket：applyWsMessage 十种消息 it.each（log/heartbeat/case_started/
 * step_started 同 index 去重排序/step_result failedSteps 去重/iteration_result 双分支累加/
 * case_finished 以 caseItems 权威值重算 overall/run_finished 收敛生成 conclusion/
 * device_error 收敛 error/未知 type 安全忽略）、同 runId 复用不重开、closeTaskWebSocket
 * 清理 map 与 handler、重连按 1s/2s/4s/8s/16s 退避 5 次后放弃（常量以源码为准）。
 * FakeWebSocket 补 readyState/OPEN/幂等 close 忠实模拟真实 WebSocket（复用判断与
 * 重连路径读这三个成员）；全局单例 window._task_ws_map/_task_ws_handlers 在
 * beforeEach closeAllTaskWebSockets() + instances 重置，防跨用例串扰。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  applyWsMessage,
  closeAllTaskWebSockets,
  closeTaskWebSocket,
  connectTaskWebSocket,
  getWsMap,
} from '@/modules/test-runner/composables/useTaskWebSocket'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  // brief 的 FakeWebSocket 未含 OPEN/readyState：源码复用判断读
  // existing.readyState <= WebSocket.OPEN，缺失时恒为 false，复用用例无法成立，
  // 故补齐真实 WebSocket 语义的这两个成员（OPEN=1 连接态）
  static OPEN = 1
  url = ''
  readyState = FakeWebSocket.OPEN
  onopen: ((ev: unknown) => void) | null = null
  onmessage: ((ev: unknown) => void) | null = null
  onclose: ((ev: unknown) => void) | null = null
  onerror: ((ev: unknown) => void) | null = null
  constructor(url: string) { this.url = url; FakeWebSocket.instances.push(this) }
  close = vi.fn(function (this: FakeWebSocket) {
    // 与真实 WebSocket 一致：关闭后重复 close 不再触发 onclose。
    // 重连路径会对已关闭旧实例调 existing.close()，非幂等会双触发 onclose、退避错乱
    if (this.readyState === 3) return
    this.readyState = 3
    this.onclose?.({ code: 1000, reason: 'test' })
  })
  send = vi.fn()
}
vi.stubGlobal('WebSocket', FakeWebSocket)
vi.mock('@/shared/ws-url', () => ({ wsUrl: vi.fn((p: string) => 'ws://test' + p) }))
vi.mock('@/shared/auth/token-storage', () => ({ getToken: vi.fn(() => 'tok') }))

function makeTask(overrides = {}) {
  return {
    id: 't1', name: '任务A', taskType: 'ui_automation', mode: 'case',
    deviceSerial: 'S1', caseIds: [2], loopCount: 1, intervalSeconds: 5,
    running: true, runId: 'R1', status: 'running',
    caseItems: [
      { id: 2, title: 'TC-2', status: 'waiting', pass: 0, fail: 0, total: 5, rate: 0 },
      { id: 7, title: 'TC-7', status: 'waiting', pass: 0, fail: 0, total: 3, rate: 0 },
    ],
    stepStates: [], logs: [],
    failedSteps: [],
    overallPass: 0, overallFail: 0,
    createdAt: '', creator: '',
    currentCaseTitle: '', currentIteration: 0, outcome: '', round: 0,
    conclusion: '',
    _connectionHealthy: true, _lastHeartbeat: 0,
    ...overrides,
  }
}

/** 源码 WsHandlerHooks 六桩全建，逐 case 断言调用 */
function makeHooks() {
  return {
    addLog: vi.fn(),
    save: vi.fn(),
    onPollQueue: vi.fn(),
    onCaseStarted: vi.fn(),
    onRunFinished: vi.fn(),
    onDeviceError: vi.fn(),
  }
}

interface WsCase {
  name: string
  prepare: () => { task: ReturnType<typeof makeTask>; msg: Record<string, unknown>; hooks: ReturnType<typeof makeHooks> }
  assert: (ctx: { task: ReturnType<typeof makeTask>; hooks: ReturnType<typeof makeHooks> }) => void
}

const wsCases: WsCase[] = [
  {
    name: 'log：仅调 addLog(message)，任务体不变',
    prepare: () => ({ task: makeTask(), msg: { type: 'log', message: '打开应用' }, hooks: makeHooks() }),
    assert: ({ task, hooks }) => {
      expect(hooks.addLog).toHaveBeenCalledTimes(1)
      expect(hooks.addLog).toHaveBeenCalledWith('打开应用')
      expect(task.status).toBe('running')
      expect(hooks.save).not.toHaveBeenCalled()
    },
  },
  {
    name: 'heartbeat：更新心跳时间戳与连接健康标记',
    prepare: () => ({ task: makeTask({ _connectionHealthy: false }), msg: { type: 'heartbeat' }, hooks: makeHooks() }),
    assert: ({ task, hooks }) => {
      expect(task._lastHeartbeat).toBe(Date.now())
      expect(task._connectionHealthy).toBe(true)
      expect(hooks.addLog).not.toHaveBeenCalled()
    },
  },
  {
    name: 'case_started：用例转 running 清 pass/fail、清空步骤、标题与轮次复位',
    prepare: () => {
      const task = makeTask({ stepStates: [{ index: 0, result: 'pass' }], currentCaseTitle: '旧用例', currentIteration: 3 })
      return { task, msg: { type: 'case_started', case_id: '2' }, hooks: makeHooks() }
    },
    assert: ({ task, hooks }) => {
      const ci = task.caseItems.find((c) => String(c.id) === '2')
      expect(ci.status).toBe('running')
      expect(ci.pass).toBe(0)
      expect(ci.fail).toBe(0)
      expect(task.stepStates).toEqual([])
      expect(task.currentCaseTitle).toBe('TC-2')
      expect(task.currentIteration).toBe(1)
      expect(hooks.onCaseStarted).toHaveBeenCalledWith(ci)
      expect(hooks.save).toHaveBeenCalledTimes(1)
    },
  },
  {
    name: 'step_started：同 index 去重替换、按 index 排序、currentIteration 跟随',
    prepare: () => {
      const task = makeTask({
        stepStates: [
          { index: 3, total: 4, type: 'assert', desc: '步骤三', result: 'running' },
          { index: 1, total: 4, type: 'nav', desc: '旧步骤一', result: 'pass' },
          { index: 0, total: 4, type: 'nav', desc: '打开页面', result: 'pass' },
        ],
      })
      return {
        task,
        msg: { type: 'step_started', step_index: 1, total_steps: 4, step_type: 'click', description: '点击按钮', iteration: 2 },
        hooks: makeHooks(),
      }
    },
    assert: ({ task }) => {
      expect(task.stepStates).toHaveLength(3)
      expect(task.stepStates.map((s) => s.index)).toEqual([0, 1, 3])
      expect(task.stepStates[1]).toMatchObject({ index: 1, total: 4, type: 'click', desc: '点击按钮', result: 'running' })
      expect(task.currentIteration).toBe(2)
    },
  },
  {
    name: 'step_result：失败进 failedSteps 且按 case+iteration+index 去重，pass 不入',
    prepare: () => {
      const task = makeTask({
        currentIteration: 1,
        stepStates: [{ index: 0, total: 3, type: 'nav', desc: '打开页面', result: 'running' }],
      })
      return {
        task,
        msg: { type: 'step_result', case_id: '2', step_index: 1, total_steps: 3, step_type: 'assert', description: '校验文本', result: 'fail' },
        hooks: makeHooks(),
      }
    },
    assert: ({ task }) => {
      // 同 case+iteration+index 重复失败：去重不重复入 failedSteps
      applyWsMessage(task, { type: 'step_result', case_id: '2', step_index: 1, total_steps: 3, step_type: 'assert', description: '校验文本', result: 'fail' }, {})
      // pass 结果：不进 failedSteps
      applyWsMessage(task, { type: 'step_result', case_id: '2', step_index: 2, total_steps: 3, step_type: 'verify', description: '验证登录', result: 'pass' }, {})
      expect(task.failedSteps).toHaveLength(1)
      expect(task.failedSteps[0]).toMatchObject({
        caseTitle: 'TC-2', iteration: 1, stepIndex: 1, stepType: 'assert', description: '校验文本', result: 'fail',
      })
      expect(task.stepStates.map((s) => s.index)).toEqual([0, 1, 2])
      expect(task.stepStates.find((s) => s.index === 2).result).toBe('pass')
    },
  },
  {
    name: 'iteration_result：pass/fail 双分支累加 ci 与 overall，rate 重算并 save',
    prepare: () => {
      const task = makeTask({
        caseItems: [{ id: 2, title: 'TC-2', status: 'running', pass: 2, fail: 1, total: 5, rate: 60 }],
        overallPass: 2,
        overallFail: 1,
      })
      return { task, msg: { type: 'iteration_result', case_id: '2', iteration: 3, result: 'pass' }, hooks: makeHooks() }
    },
    assert: ({ task, hooks }) => {
      const ci = task.caseItems[0]
      expect(ci.pass).toBe(3)
      expect(ci.fail).toBe(1)
      expect(ci.rate).toBe(80) // round((3+1)/5*100)
      expect(task.overallPass).toBe(3)
      expect(task.overallFail).toBe(1)
      expect(task.currentIteration).toBe(3)

      applyWsMessage(task, { type: 'iteration_result', case_id: '2', iteration: 4, result: 'fail' }, hooks)
      expect(ci.pass).toBe(3)
      expect(ci.fail).toBe(2)
      expect(ci.rate).toBe(100)
      expect(task.overallPass).toBe(3)
      expect(task.overallFail).toBe(2)
      expect(task.currentIteration).toBe(4)
      expect(hooks.save).toHaveBeenCalledTimes(2)
    },
  },
  {
    name: 'case_finished：单例收口 done/rate=100 并以 caseItems 权威值重算 overall',
    prepare: () => {
      const task = makeTask({
        caseItems: [
          { id: 2, title: 'TC-2', status: 'running', pass: 2, fail: 1, total: 5, rate: 60 },
          { id: 7, title: 'TC-7', status: 'running', pass: 1, fail: 2, total: 3, rate: 100 },
        ],
        overallPass: 99,
        overallFail: 88,
      })
      return { task, msg: { type: 'case_finished', case_id: '2', pass: 4, fail: 1 }, hooks: makeHooks() }
    },
    assert: ({ task, hooks }) => {
      const ci = task.caseItems.find((c) => String(c.id) === '2')
      expect(ci.status).toBe('done')
      expect(ci.pass).toBe(4)
      expect(ci.fail).toBe(1)
      expect(ci.rate).toBe(100)
      expect(task.overallPass).toBe(5) // 4 + 1 重算，覆盖陈旧 99
      expect(task.overallFail).toBe(3) // 1 + 2 重算，覆盖陈旧 88
      expect(hooks.save).toHaveBeenCalledTimes(1)
    },
  },
  {
    name: 'run_finished：running/status/caseItems 收敛、生成 conclusion、三回调触发',
    prepare: () => {
      const task = makeTask({
        caseItems: [{ id: 2, title: 'TC-2', status: 'running', pass: 3, fail: 1, total: 4, rate: 100 }],
        overallPass: 3,
        overallFail: 1,
        currentCaseTitle: 'TC-2',
        currentIteration: 2,
        conclusion: '',
      })
      return { task, msg: { type: 'run_finished' }, hooks: makeHooks() }
    },
    assert: ({ task, hooks }) => {
      expect(task.running).toBe(false)
      expect(task.status).toBe('done')
      expect(task.outcome).toBe('completed')
      expect(task.caseItems.every((c) => c.status === 'done')).toBe(true)
      expect(task.currentCaseTitle).toBe('')
      expect(task.currentIteration).toBe(0)
      expect(task.conclusion).toBe('❌ 测试不通过：1 个用例执行失败')
      expect(hooks.addLog).toHaveBeenCalledWith('🏁 完成 ✅3 ❌1', 'success')
      expect(hooks.onRunFinished).toHaveBeenCalledWith(task)
      expect(hooks.save).toHaveBeenCalledTimes(1)
      expect(hooks.onPollQueue).toHaveBeenCalledTimes(1)
    },
  },
  {
    name: 'device_error：收敛 done/error、error 日志与回调触发',
    prepare: () => ({ task: makeTask({ outcome: '' }), msg: { type: 'device_error', message: '设备断开连接' }, hooks: makeHooks() }),
    assert: ({ task, hooks }) => {
      expect(task.running).toBe(false)
      expect(task.status).toBe('done')
      expect(task.outcome).toBe('error')
      expect(hooks.addLog).toHaveBeenCalledWith('💥 设备断开连接', 'error')
      expect(hooks.onDeviceError).toHaveBeenCalledWith(task)
      expect(hooks.save).toHaveBeenCalledTimes(1)
      expect(hooks.onPollQueue).toHaveBeenCalledTimes(1)
    },
  },
  {
    name: '未知 type：安全忽略，任务与 hooks 均无副作用',
    prepare: () => ({ task: makeTask(), msg: { type: 'unknown_type', whatever: 1 }, hooks: makeHooks() }),
    assert: ({ task, hooks }) => {
      expect(task.status).toBe('running')
      expect(task.currentCaseTitle).toBe('')
      expect(hooks.addLog).not.toHaveBeenCalled()
      expect(hooks.save).not.toHaveBeenCalled()
      expect(hooks.onPollQueue).not.toHaveBeenCalled()
      expect(hooks.onCaseStarted).not.toHaveBeenCalled()
      expect(hooks.onRunFinished).not.toHaveBeenCalled()
      expect(hooks.onDeviceError).not.toHaveBeenCalled()
    },
  },
]

describe('[P0] useTaskWebSocket', () => {
  beforeEach(() => {
    // fake timers 全程启用：close 触发的重连 setTimeout 不落真实时钟，
    // 仅重连用例按档推进，其余用例在 afterEach clearAllTimers 中销毁
    vi.useFakeTimers()
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    FakeWebSocket.instances = []
    closeAllTaskWebSockets()
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  // ── 消息分发：十种 case 表驱动 ──

  describe('applyWsMessage：十种消息 case', () => {
    it.each(wsCases)('$name', ({ prepare, assert }) => {
      const ctx = prepare()
      applyWsMessage(ctx.task, ctx.msg, ctx.hooks)
      assert(ctx)
    })
  })

  // ── 连接复用：同 runId 不重开 ──

  it('connectTaskWebSocket：同 runId 已连接复用不重开，URL 携带 token', () => {
    const createHandler = vi.fn()
    const ws1 = connectTaskWebSocket('t1', 'R1', createHandler)
    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(ws1.url).toBe('ws://test/ws/test-run/R1?token=tok')

    const ws2 = connectTaskWebSocket('t1', 'R1', createHandler)

    expect(ws2).toBe(ws1)
    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(ws1.close).not.toHaveBeenCalled()
    expect(getWsMap().t1).toBe(ws1)
  })

  // ── 关闭清理：map 与 handler 双清 ──

  it('closeTaskWebSocket：关闭连接并清理 map 与 handler', () => {
    const createHandler = vi.fn()
    connectTaskWebSocket('t1', 'R1', createHandler)
    expect(getWsMap().t1).toBeDefined()
    expect((window as unknown as Record<string, Record<string, unknown>>)._task_ws_handlers.t1).toBe(createHandler)

    closeTaskWebSocket('t1')

    expect(getWsMap().t1).toBeUndefined()
    expect((window as unknown as Record<string, Record<string, unknown>>)._task_ws_handlers.t1).toBeUndefined()
    expect(FakeWebSocket.instances[0].close).toHaveBeenCalledTimes(1)
  })

  // ── 断线重连：指数退避 5 次上限 ──

  it('重连：onclose 后按 1s/2s/4s/8s/16s 逐档退避重连，5 次后放弃', async () => {
    const createHandler = vi.fn()
    connectTaskWebSocket('t1', 'R1', createHandler)
    expect(FakeWebSocket.instances).toHaveLength(1)

    const backoff = [1000, 2000, 4000, 8000, 16000]
    for (let attempt = 1; attempt <= 5; attempt++) {
      const ws = FakeWebSocket.instances[FakeWebSocket.instances.length - 1]
      ws.close()
      expect(console.warn).toHaveBeenCalledWith(
        `[WS] Disconnected for t1, reconnecting in ${backoff[attempt - 1] / 1000}s (attempt ${attempt}/5)`,
      )
      await vi.advanceTimersByTimeAsync(backoff[attempt - 1])
      expect(FakeWebSocket.instances).toHaveLength(attempt + 1)
    }
    expect(createHandler).toHaveBeenCalledWith({ type: '_ws_disconnected' })

    // 第 6 次断开：已达 5 次上限，报错且不再排重连定时器
    const last = FakeWebSocket.instances[FakeWebSocket.instances.length - 1]
    last.close()
    expect(createHandler).toHaveBeenCalledTimes(6)
    expect(console.error).toHaveBeenCalledWith('[WS] Max reconnect attempts reached for t1')
    await vi.advanceTimersByTimeAsync(60000)
    expect(FakeWebSocket.instances).toHaveLength(6)
    expect(getWsMap().t1).toBe(last)
  })
})
