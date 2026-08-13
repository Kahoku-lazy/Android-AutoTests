/**
 * [P1] 建议测 — test-runner WS seq gap 检测与重连注入、断连/重连消息分支
 * 目录：tests/test-runner/p1/
 *
 * useTaskWebSocket：seq gap 检测（seq 跳号置 ws._seqGapDetected 并 console.warn 丢失数；
 * 重连后 onopen 向 handler 注入 { type: '_ws_reconnected' }）；applyWsMessage 补 P0 未
 * 覆盖的两个 switch case（_ws_disconnected 仅运行中翻转 _connectionHealthy 并 warning
 * 日志 + save；_ws_reconnected 置健康标志与 _wsJustReconnected，运行中 success 日志）。
 * FakeWebSocket 继承 P0 三处补齐（static OPEN=1 / readyState=1 / close 幂等，复用判断
 * 与重连路径读这三个成员）；单例卫生同 P0（beforeEach closeAllTaskWebSockets +
 * instances 重置，fake timers 全程启用）。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  applyWsMessage,
  closeAllTaskWebSockets,
  connectTaskWebSocket,
} from '@/modules/test-runner/composables/useTaskWebSocket'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  // 继承 P0 三处补齐：源码复用判断读 existing.readyState <= WebSocket.OPEN，
  // 缺失时恒为 false，重连路径无法成立（OPEN=1 连接态）
  static OPEN = 1
  url = ''
  readyState = FakeWebSocket.OPEN
  _seqGapDetected?: boolean
  _lastSeq?: number
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
    overallPass: 0, overallFail: 0,
    createdAt: '', creator: '',
    currentCaseTitle: '', currentIteration: 0, outcome: '', round: 0,
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

describe('[P1] useTaskWebSocket', () => {
  beforeEach(() => {
    // fake timers 全程启用：close 触发的重连 setTimeout 不落真实时钟，
    // seq gap 用例按档推进，其余用例在 afterEach clearAllTimers 中销毁
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

  // ── seq gap：跳号检测 + 重连注入 ──

  it('seq gap：跳号置 _seqGapDetected 并 warn，重连 open 向 handler 注入 _ws_reconnected', async () => {
    const createHandler = vi.fn()
    const ws = connectTaskWebSocket('t1', 'R1', createHandler)
    expect(FakeWebSocket.instances).toHaveLength(1)

    // 首次 open 无 gap 标记：不注入
    expect(ws.onopen).toBeTypeOf('function')
    ws.onopen?.({})
    expect(createHandler).not.toHaveBeenCalledWith({ type: '_ws_reconnected' })

    // 连续 seq 建立基线：不置位
    expect(ws.onmessage).toBeTypeOf('function')
    ws.onmessage?.({ data: JSON.stringify({ type: 'heartbeat', seq: 5 }) })
    expect(ws._seqGapDetected).toBeUndefined()
    expect(ws._lastSeq).toBe(5)

    // 跳号 5 → 8：置位并 warn 丢失数
    ws.onmessage?.({ data: JSON.stringify({ type: 'heartbeat', seq: 8 }) })
    expect(ws._seqGapDetected).toBe(true)
    expect(ws._lastSeq).toBe(8)
    expect(console.warn).toHaveBeenCalledWith('[WS] seq gap: 5 → 8 (2 lost) for t1')

    // 断开触发重连：先收到 _ws_disconnected，1s 后新实例继承 _seqGapDetected
    ws.close()
    expect(createHandler).toHaveBeenCalledWith({ type: '_ws_disconnected' })
    await vi.advanceTimersByTimeAsync(1000)
    expect(FakeWebSocket.instances).toHaveLength(2)
    const newWs = FakeWebSocket.instances[1]
    expect(newWs._seqGapDetected).toBe(true)

    // 重连 open：gap 标记 → 向 handler 注入 _ws_reconnected
    expect(newWs.onopen).toBeTypeOf('function')
    newWs.onopen?.({})
    expect(createHandler).toHaveBeenCalledWith({ type: '_ws_reconnected' })
  })

  // ── applyWsMessage：P0 未覆盖的断连/重连两个 case ──

  describe('applyWsMessage 断连/重连 case', () => {
    it('_ws_disconnected：运行中翻转 _connectionHealthy 为 false 并 warning 日志', () => {
      const task = makeTask({ _connectionHealthy: true })
      const hooks = makeHooks()

      applyWsMessage(task, { type: '_ws_disconnected' }, hooks)

      expect(task._connectionHealthy).toBe(false)
      expect(hooks.addLog).toHaveBeenCalledWith('⚠️ 连接断开，正在重连…', 'warning')
      expect(hooks.save).toHaveBeenCalledTimes(1)
    })

    it('_ws_disconnected：任务未运行时不翻转健康标志也无日志', () => {
      const task = makeTask({ running: false, _connectionHealthy: true })
      const hooks = makeHooks()

      applyWsMessage(task, { type: '_ws_disconnected' }, hooks)

      expect(task._connectionHealthy).toBe(true)
      expect(hooks.addLog).not.toHaveBeenCalled()
      expect(hooks.save).not.toHaveBeenCalled()
    })

    it('_ws_reconnected：置健康标志与 _wsJustReconnected，运行中 success 日志', () => {
      const task = makeTask({ _connectionHealthy: false, _wsJustReconnected: false })
      const hooks = makeHooks()

      applyWsMessage(task, { type: '_ws_reconnected' }, hooks)

      expect(task._connectionHealthy).toBe(true)
      expect(task._wsJustReconnected).toBe(true)
      expect(hooks.addLog).toHaveBeenCalledWith('🔗 已重新连接', 'success')
      expect(hooks.save).not.toHaveBeenCalled()
    })
  })
})
