/**
 * [P0] 必测 — device-pool API 端点封装（表驱动，mock api-client，不断真网络）
 * 目录：tests/device-pool/p0/
 *
 * api.ts 8 个端点函数（10 条表驱动用例）：断言 client 方法、URL、body 透传，且恰好调用一次。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import client from '@/shared/api-client'
import * as dpApi from '@/modules/device-pool/api'

vi.mock('@/shared/api-client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

type ClientMethod = 'get' | 'post' | 'put' | 'delete'

interface ApiCase {
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
    name: 'apiConnectDevice：透传 activate',
    invoke: () => dpApi.apiConnectDevice('S1', { activate: false }),
    method: 'post',
    url: '/devices/S1',
    body: { activate: false },
  },
  {
    name: 'apiConnectDevice：缺省参数默认 activate true',
    invoke: () => dpApi.apiConnectDevice('S1', {}),
    method: 'post',
    url: '/devices/S1',
    body: { activate: true },
  },
  {
    name: 'apiActivate：POST 激活 URL',
    invoke: () => dpApi.apiActivate('S1'),
    method: 'post',
    url: '/devices/S1/activate',
  },
  {
    name: 'apiLockDevice：透传 locked',
    invoke: () => dpApi.apiLockDevice('S1', true),
    method: 'post',
    url: '/devices/S1/lock',
    body: { locked: true },
  },
  {
    name: 'apiReleaseDevice：POST 释放 URL',
    invoke: () => dpApi.apiReleaseDevice('S1'),
    method: 'post',
    url: '/devices/S1/release',
  },
  {
    name: 'apiDisconnect：POST 删除 URL',
    invoke: () => dpApi.apiDisconnect('S1'),
    method: 'post',
    url: '/devices/S1/disconnect',
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
