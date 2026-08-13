/**
 * [P0] 必测 — device-pool API 端点封装（表驱动，mock api-client，不断真网络）
 * 目录：tests/device-pool/p0/
 *
 * api.ts 12 个端点函数：断言 client 方法、URL、body 透传，且恰好调用一次。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import client from '@/shared/api-client'
import * as dpApi from '@/modules/device-pool/api'

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
  {
    name: 'apiListDevices：GET /devices',
    invoke: () => dpApi.apiListDevices(),
    method: 'get',
    url: '/devices',
  },
  {
    name: 'apiScanDevices：无 target 时发送空 body',
    invoke: () => dpApi.apiScanDevices(),
    method: 'post',
    url: '/devices/scan',
    body: {},
  },
  {
    name: 'apiScanDevices：带 target 时透传 body',
    invoke: () => dpApi.apiScanDevices('10.0.0.1'),
    method: 'post',
    url: '/devices/scan',
    body: { target: '10.0.0.1' },
  },
  {
    name: 'apiConnectDevice：完整参数透传 body 含 activate',
    invoke: () => dpApi.apiConnectDevice('S1', { activate: true, userId: '1', timeout: 999 }),
    method: 'post',
    url: '/devices/S1',
    body: { activate: true, user_id: '1', timeout: 999 },
  },
  {
    name: 'apiConnectDevice：缺省参数注入默认 timeout 300',
    invoke: () => dpApi.apiConnectDevice('S1', {}),
    method: 'post',
    url: '/devices/S1',
    body: { activate: true, user_id: '', timeout: 300 },
  },
  {
    name: 'apiActivate：POST 激活 URL',
    invoke: () => dpApi.apiActivate('S1'),
    method: 'post',
    url: '/devices/S1/activate',
  },
  {
    name: 'apiLockDevice：user_id/timeout/type 透传 body',
    invoke: () => dpApi.apiLockDevice('S1', '1', 900, 'user'),
    method: 'post',
    url: '/devices/S1/lock',
    body: { user_id: '1', timeout: 900, type: 'user' },
  },
  {
    name: 'apiReleaseDevice：透传 reason/unlock/force',
    invoke: () =>
      dpApi.apiReleaseDevice('S1', { userId: '1', reason: 'done', unlock: true, force: false }),
    method: 'post',
    url: '/devices/S1/release',
    body: { user_id: '1', reason: 'done', unlock: true, force: false },
  },
  {
    name: 'apiDisconnect：布尔字段映射 is_admin',
    invoke: () =>
      dpApi.apiDisconnect('S1', { force: true, reason: 'x', userId: '1', isAdmin: false }),
    method: 'post',
    url: '/devices/S1/disconnect',
    body: { force: true, reason: 'x', user_id: '1', is_admin: false },
  },
  {
    name: 'apiGetQueue：GET /devices/queue',
    invoke: () => dpApi.apiGetQueue(),
    method: 'get',
    url: '/devices/queue',
  },
  {
    name: 'apiJoinQueue：透传 user_id',
    invoke: () => dpApi.apiJoinQueue('S1', '1'),
    method: 'post',
    url: '/devices/S1/queue',
    body: { user_id: '1' },
  },
  {
    name: 'apiLeaveQueue：透传 user_id',
    invoke: () => dpApi.apiLeaveQueue('S1', '1'),
    method: 'post',
    url: '/devices/S1/queue/leave',
    body: { user_id: '1' },
  },
  {
    name: 'apiHeartbeat：GET 心跳 URL',
    invoke: () => dpApi.apiHeartbeat(),
    method: 'get',
    url: '/devices/heartbeat',
  },
]

describe('[P0] device-pool api 端点', () => {
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
})
