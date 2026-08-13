/**
 * [P1] 建议测 — 设备池状态写操作联动（mock 整个 api 模块，不断真网络）
 * 目录：tests/device-pool/p1/
 *
 * useDevicePoolState：do* 成功联动 fetchDevices/fetchQueue 刷新、doHeartbeat 吞异常仅 debug。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as dpApi from '@/modules/device-pool/api'
import {
  useDevicePoolState,
  type UseDevicePoolStateReturn,
} from '@/modules/device-pool/composables/useDevicePoolState'
import type { DeviceRecord } from '@/shared/types/device'

vi.mock('@/modules/device-pool/api', () => ({
  apiListDevices: vi.fn(),
  apiScanDevices: vi.fn(),
  apiConnectDevice: vi.fn(),
  apiActivate: vi.fn(),
  apiLockDevice: vi.fn(),
  apiReleaseDevice: vi.fn(),
  apiDisconnect: vi.fn(),
  apiGetQueue: vi.fn(),
  apiJoinQueue: vi.fn(),
  apiLeaveQueue: vi.fn(),
  apiHeartbeat: vi.fn(),
}))

function makeListRes(
  status: boolean,
  devices: DeviceRecord[],
  current = '',
  queueLength = 0,
) {
  return { data: { status, devices, current, queue_length: queueLength } }
}

type LinkRow = {
  name: string
  op: keyof typeof dpApi
  refresh: 'apiListDevices' | 'apiGetQueue'
  refreshRes: () => unknown
  run: (s: UseDevicePoolStateReturn) => Promise<unknown>
}

const linkRows: LinkRow[] = [
  {
    name: 'doConnect',
    op: 'apiConnectDevice',
    refresh: 'apiListDevices',
    refreshRes: () => makeListRes(true, [], '', 0),
    run: (s) => s.doConnect('S1', { activate: true }),
  },
  {
    name: 'doActivate',
    op: 'apiActivate',
    refresh: 'apiListDevices',
    refreshRes: () => makeListRes(true, [], '', 0),
    run: (s) => s.doActivate('S1'),
  },
  {
    name: 'doLock',
    op: 'apiLockDevice',
    refresh: 'apiListDevices',
    refreshRes: () => makeListRes(true, [], '', 0),
    run: (s) => s.doLock('S1', 'u1', 3600, 'user'),
  },
  {
    name: 'doRelease',
    op: 'apiReleaseDevice',
    refresh: 'apiListDevices',
    refreshRes: () => makeListRes(true, [], '', 0),
    run: (s) => s.doRelease('S1', { unlock: true }),
  },
  {
    name: 'doDisconnect',
    op: 'apiDisconnect',
    refresh: 'apiListDevices',
    refreshRes: () => makeListRes(true, [], '', 0),
    run: (s) => s.doDisconnect('S1', { force: false }),
  },
  {
    name: 'doJoinQueue',
    op: 'apiJoinQueue',
    refresh: 'apiGetQueue',
    refreshRes: () => ({ data: { status: true, queue: [], count: 0 } }),
    run: (s) => s.doJoinQueue('S1', 'u1'),
  },
  {
    name: 'doLeaveQueue',
    op: 'apiLeaveQueue',
    refresh: 'apiGetQueue',
    refreshRes: () => ({ data: { status: true, queue: [], count: 0 } }),
    run: (s) => s.doLeaveQueue('S1', 'u1'),
  },
]

describe('[P1] useDevicePoolState', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it.each(linkRows)('$name 成功：联动刷新恰好一次', async (row) => {
    const opFn = dpApi[row.op] as unknown as ReturnType<typeof vi.fn>
    opFn.mockResolvedValue({ data: { status: true } })
    const refreshFn = dpApi[row.refresh] as unknown as ReturnType<typeof vi.fn>
    refreshFn.mockResolvedValue(row.refreshRes())
    const otherFn = dpApi[
      row.refresh === 'apiListDevices' ? 'apiGetQueue' : 'apiListDevices'
    ] as unknown as ReturnType<typeof vi.fn>

    const s = useDevicePoolState()
    const result = await row.run(s)

    expect(result).toEqual({ status: true })
    expect(refreshFn).toHaveBeenCalledTimes(1)
    expect(otherFn).not.toHaveBeenCalled()
  })

  it('doHeartbeat 异常：吞掉不抛，仅 console.debug 记录', async () => {
    vi.mocked(dpApi.apiHeartbeat).mockRejectedValue(new Error('net down'))
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {})

    const s = useDevicePoolState()
    await expect(s.doHeartbeat()).resolves.toBeUndefined()

    expect(dpApi.apiHeartbeat).toHaveBeenCalledTimes(1)
    expect(debugSpy).toHaveBeenCalledTimes(1)
    expect(debugSpy.mock.calls[0][0]).toContain('[device-pool] heartbeat:')

    debugSpy.mockRestore()
  })
})
