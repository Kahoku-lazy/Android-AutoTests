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
import { RUNNER_OCCUPIED_PREFIXES } from '@/modules/device-pool/constants'
import type { DeviceRecord } from '@/shared/types/device'
import type { UseDevicePoolStateReturn } from '@/modules/device-pool/composables/useDevicePoolState'

vi.mock('@/shared/animations', () => ({ countUpFormatted: vi.fn(), staggerReveal: vi.fn(), animate: vi.fn() }))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/auth/token-storage', () => ({ getActive: vi.fn(() => ({ username: 'u1' })), getActiveUsername: vi.fn(() => 'u1') }))

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

  it('handleLockClick 他人锁定：仅弹 warning 不发请求', async () => {
    const pool = makePool()
    const actions = useDeviceActions(pool)
    const device = makeDevice('S1', { locked_by: 'other-user' })

    await actions.handleLockClick(device)

    expect(vi.mocked(ElMessage.warning)).toHaveBeenCalledWith(
      '设备已被 other-user 锁定，只有锁定者可以解除',
    )
    expect(pool.doLock).not.toHaveBeenCalled()
    expect(pool.doRelease).not.toHaveBeenCalled()
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

  it('handleRelease：runner 前缀占用拒绝释放并弹 error', async () => {
    const pool = makePool({
      devices: ref([makeDevice('S1', { occupied_by: `${RUNNER_OCCUPIED_PREFIXES[1]}42` })]),
    })
    const actions = useDeviceActions(pool)

    await actions.handleRelease('S1')

    expect(vi.mocked(ElMessage.error)).toHaveBeenCalledWith(
      '设备正在执行用例，无法解除占用。请等待用例执行完毕。',
    )
    expect(pool.doRelease).not.toHaveBeenCalled()
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
