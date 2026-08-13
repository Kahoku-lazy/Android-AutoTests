/**
 * [P0] 必测 — 设备池状态管理 composable（mock 整个 api 模块，不断真网络）
 * 目录：tests/device-pool/p0/
 *
 * useDevicePoolState：fetchDevices 成功写入 state / 失败置 error、
 * doScan 异常降级返回、doActivate 成功写 currentSerial 并触发刷新。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as dpApi from '@/modules/device-pool/api'
import { useDevicePoolState } from '@/modules/device-pool/composables/useDevicePoolState'
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

function makeDevice(serial: string): DeviceRecord {
  return {
    serial,
    model: 'Pixel 6',
    status: 'ONLINE',
    connection_type: 'USB',
    last_seen: '2026-08-13 10:00',
  }
}

function makeListRes(
  status: boolean,
  devices: DeviceRecord[],
  current = '',
  queueLength = 0,
) {
  return { data: { status, devices, current, queue_length: queueLength } }
}

describe('[P0] useDevicePoolState', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchDevices 成功：写入 devices/currentSerial/queueLength，loading 复位', async () => {
    vi.mocked(dpApi.apiListDevices).mockResolvedValue(
      makeListRes(true, [makeDevice('S1'), makeDevice('S2')], 'S1', 3) as never,
    )

    const s = useDevicePoolState()
    const p = s.fetchDevices()
    expect(s.loading.value).toBe(true)

    await p

    expect(s.devices.value).toEqual([makeDevice('S1'), makeDevice('S2')])
    expect(s.currentSerial.value).toBe('S1')
    expect(s.queueLength.value).toBe(3)
    expect(s.loading.value).toBe(false)
    expect(s.error.value).toBeNull()
  })

  it('fetchDevices 失败：error 置位，loading 复位', async () => {
    vi.mocked(dpApi.apiListDevices).mockRejectedValue(new Error('boom'))

    const s = useDevicePoolState()
    await s.fetchDevices()

    expect(s.error.value).toBe('设备列表加载失败，请稍后重试')
    expect(s.loading.value).toBe(false)
    expect(s.devices.value).toEqual([])
  })

  it("doScan 异常：返回降级 {status:false,message:'扫描失败'} 且不抛异常", async () => {
    vi.mocked(dpApi.apiScanDevices).mockRejectedValue(new Error('boom'))

    const s = useDevicePoolState()
    const result = await s.doScan()

    expect(result).toEqual({ status: false, message: '扫描失败' })
    expect(s.scanning.value).toBe(false)
  })

  it('doActivate 成功：写入 currentSerial 并触发刷新', async () => {
    vi.mocked(dpApi.apiActivate).mockResolvedValue({ data: { status: true } } as never)
    vi.mocked(dpApi.apiListDevices).mockResolvedValue(
      makeListRes(true, [makeDevice('S1')], 'S1', 0) as never,
    )

    const s = useDevicePoolState()
    const result = await s.doActivate('S1')

    expect(result).toEqual({ status: true })
    expect(s.currentSerial.value).toBe('S1')
    expect(dpApi.apiListDevices).toHaveBeenCalledTimes(1)
  })
})
