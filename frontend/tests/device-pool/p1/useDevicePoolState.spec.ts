/**
 * [P1] 建议测 — 设备池状态写操作联动（mock 整个 api 模块，不断真网络）
 * 目录：tests/device-pool/p1/
 *
 * useDevicePoolState：do* 成功联动 fetchDevices 刷新、doHeartbeat 吞异常仅 debug。
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
  apiHeartbeat: vi.fn(),
}))

function makeListRes(status: boolean, devices: DeviceRecord[], current = '') {
  return { data: { status, data: { devices, current } } }
}

type LinkRow = {
  name: string
  op: keyof typeof dpApi
  run: (s: UseDevicePoolStateReturn) => Promise<unknown>
}

const linkRows: LinkRow[] = [
  { name: 'doConnect', op: 'apiConnectDevice', run: (s) => s.doConnect('S1', { activate: true }) },
  { name: 'doActivate', op: 'apiActivate', run: (s) => s.doActivate('S1') },
  { name: 'doLock', op: 'apiLockDevice', run: (s) => s.doLock('S1', true) },
  { name: 'doRelease', op: 'apiReleaseDevice', run: (s) => s.doRelease('S1') },
  { name: 'doDisconnect', op: 'apiDisconnect', run: (s) => s.doDisconnect('S1') },
]

describe('[P1] useDevicePoolState', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it.each(linkRows)('$name 成功：联动刷新恰好一次', async (row) => {
    const opFn = dpApi[row.op] as unknown as ReturnType<typeof vi.fn>
    opFn.mockResolvedValue({ data: { status: true } })
    vi.mocked(dpApi.apiListDevices).mockResolvedValue(makeListRes(true, []) as never)

    const s = useDevicePoolState()
    const result = await row.run(s)

    expect(result).toEqual({ status: true })
    expect(dpApi.apiListDevices).toHaveBeenCalledTimes(1)
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
