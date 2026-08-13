/**
 * [P0] 必测 — test-runner API 端点封装（表驱动，mock api-client，不断真网络）
 * 目录：tests/test-runner/p0/
 *
 * api.ts 11 个端点函数：cancelQueue snake_case 映射、startRun body 透传单独测，
 * 其余 9 端点表驱动断言 client 方法、URL、body 三元组，且恰好调用一次。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import client from '@/shared/api-client'
import * as trApi from '@/modules/test-runner/api'

vi.mock('@/shared/api-client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

type ClientMethod = 'get' | 'post' | 'put' | 'delete'

interface ApiCase {
  /** 用例名：场景 + 全角冒号 + 预期 */
  name: string
  invoke: () => unknown
  method: ClientMethod
  url: string
  body?: unknown
}

const cases: ApiCase[] = [
  // ── 测试执行 ──
  {
    name: 'stopRun：runId 拼入 URL，无 body',
    invoke: () => trApi.stopRun('R1'),
    method: 'post',
    url: '/runner/run/R1/stop',
  },
  {
    name: 'getActiveRuns：GET /runner/active',
    invoke: () => trApi.getActiveRuns(),
    method: 'get',
    url: '/runner/active',
  },
  // ── 任务持久化 ──
  {
    name: 'listTasks：GET /runner/tasks',
    invoke: () => trApi.listTasks(),
    method: 'get',
    url: '/runner/tasks',
  },
  {
    name: 'saveTask：body 透传',
    invoke: () => trApi.saveTask({ id: 1, name: 't1' }),
    method: 'post',
    url: '/runner/tasks/save',
    body: { id: 1, name: 't1' },
  },
  {
    name: 'deleteTask：DELETE /runner/tasks/:id',
    invoke: () => trApi.deleteTask('T1'),
    method: 'delete',
    url: '/runner/tasks/T1',
  },
  // ── 用例定义（跨模块封装） ──
  {
    name: 'listDefinitions：GET /cases/definitions',
    invoke: () => trApi.listDefinitions(),
    method: 'get',
    url: '/cases/definitions',
  },
  {
    name: 'listApiDefinitions：GET /cases/api-testing/definitions',
    invoke: () => trApi.listApiDefinitions(),
    method: 'get',
    url: '/cases/api-testing/definitions',
  },
  {
    name: 'listWebDefinitions：GET /cases/web/definitions',
    invoke: () => trApi.listWebDefinitions(),
    method: 'get',
    url: '/cases/web/definitions',
  },
  // ── 设备列表（跨模块） ──
  {
    name: 'listDevices：GET /devices',
    invoke: () => trApi.listDevices(),
    method: 'get',
    url: '/devices',
  },
]

describe('[P0] test-runner api 端点', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it.each(cases)('$name，且恰好调用一次对应 client 方法', ({ invoke, method, url, body }) => {
    invoke()

    if (body === undefined) {
      expect(client[method]).toHaveBeenCalledWith(url)
    } else {
      expect(client[method]).toHaveBeenCalledWith(url, body)
    }
    expect(client[method]).toHaveBeenCalledTimes(1)
  })

  // ── 重点：cancelQueue snake_case 映射 ──

  it('cancelQueue：body snake_case 映射', () => {
    trApi.cancelQueue('ct1', 'S1')

    expect(client.post).toHaveBeenCalledWith('/runner/queue/cancel', {
      client_task_id: 'ct1',
      device_serial: 'S1',
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  // ── 重点：startRun body 透传 ──

  it('startRun：body 透传', () => {
    const body = { device_serial: 'S1', case_ids: [1, 2], loop_count: 2 }
    trApi.startRun(body)

    expect(client.post).toHaveBeenCalledWith('/runner/run', body)
    expect(client.post).toHaveBeenCalledTimes(1)
  })
})
