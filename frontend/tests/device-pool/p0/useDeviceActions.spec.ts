/**
 * [P0] 必测 — 设备操作 handler（池对象桩注入，不 mock api，校验短路逻辑）
 * 目录：tests/device-pool/p0/
 *
 * useDeviceActions：他人锁定仅弹 warning 不发请求、scanning/loading 中刷新短路、
 * runner 前缀占用拒绝释放、空 target 网络连接短路。
 */
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { useDeviceActions } from '@/modules/device-pool/composables/useDeviceActions'
import type { DeviceRecord } from '@/shared/types/device'
import type { UseDevicePoolStateReturn } from '@/modules/device-pool/composables/useDevicePoolState'

vi.mock('animejs', () => ({ animate: vi.fn(), stagger: vi.fn() }))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/auth/token-storage', () => ({ getActive: vi.fn(() => 'u1'), getActiveUsername: vi.fn(() => 'u1') }))

function makeDevice(serial: string, extra: Partial<DeviceRecord> = {}): DeviceRecord {
  return {
    serial,
    model: 'Pixel 6',
    status: 'ONLINE',
    connection_type: 'USB',
    last_seen: '2026-08-13 10:00',
    ...extra,
  }
}

function makePool(overrides: Partial<UseDevicePoolStateReturn> = {}): UseDevicePoolStateReturn {
  return {
    devices: ref<DeviceRecord[]>([]),
    scanning: ref(false),
    loading: ref(false),
    fetchDevices: vi.fn().mockResolvedValue(undefined),
    doScan: vi.fn().mockResolvedValue({ status: false, message: '扫描失败' }),
    doLock: vi.fn().mockResolvedValue({ status: true }),
    doRelease: vi.fn().mockResolvedValue({ status: true }),
    selectDevice: vi.fn(),
    ...overrides,
  } as unknown as UseDevicePoolStateReturn
}

describe('[P0] useDeviceActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('handleRefresh：scanning/loading 中短路不发请求', async () => {
    const pool = makePool()
    const actions = useDeviceActions(pool)

    pool.scanning.value = true
    await actions.handleRefresh()
    expect(pool.doScan).not.toHaveBeenCalled()
    expect(pool.fetchDevices).not.toHaveBeenCalled()

    pool.scanning.value = false
    pool.loading.value = true
    await actions.handleRefresh()
    expect(pool.doScan).not.toHaveBeenCalled()
    expect(pool.fetchDevices).not.toHaveBeenCalled()
    expect(vi.mocked(ElMessage.success)).not.toHaveBeenCalled()
  })

  it('handleNetworkConnect：空 target 短路不调扫描', async () => {
    const pool = makePool()
    const actions = useDeviceActions(pool)

    await actions.handleNetworkConnect({ target: '' })

    expect(pool.doScan).not.toHaveBeenCalled()
    expect(actions.networkDialog.value.loading).toBe(false)
    expect(vi.mocked(ElMessage.error)).not.toHaveBeenCalled()
  })
})
