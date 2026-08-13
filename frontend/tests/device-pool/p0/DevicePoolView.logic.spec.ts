/**
 * [P0] 必测 — 设备池页面编排器（mock 三个子 composable，挂载触发 onMounted）
 * 目录：tests/device-pool/p0/
 *
 * useDevicePoolView：KPI 按状态聚合、切换筛选过滤并重置页码、挂载联动 loadDevices/startHeartbeat。
 */
import { ref, nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  useDevicePoolState,
  type UseDevicePoolStateReturn,
} from '@/modules/device-pool/composables/useDevicePoolState'
import { useHeartbeat } from '@/modules/device-pool/composables/useHeartbeat'
import {
  useDeviceActions,
  type UseDeviceActionsReturn,
} from '@/modules/device-pool/composables/useDeviceActions'
import { useDevicePoolView } from '@/modules/device-pool/DevicePoolView.logic'
import type { DeviceRecord } from '@/shared/types/device'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('@/modules/device-pool/composables/useDevicePoolState', () => ({ useDevicePoolState: vi.fn() }))
vi.mock('@/modules/device-pool/composables/useHeartbeat', () => ({ useHeartbeat: vi.fn() }))
vi.mock('@/modules/device-pool/composables/useDeviceActions', () => ({ useDeviceActions: vi.fn() }))

function makeDevice(serial: string, status: DeviceRecord['status'] = 'ONLINE'): DeviceRecord {
  return {
    serial,
    model: 'Pixel 6',
    status,
    connection_type: 'USB',
    last_seen: '2026-08-13 10:00',
  }
}

function makePool(devices: DeviceRecord[]) {
  return {
    devices: ref(devices),
    loading: ref(false),
    scanning: ref(false),
    queueEntries: ref([]),
    queueLength: ref(0),
    selectedSerial: ref<string | null>(null),
    error: ref<string | null>(null),
    doHeartbeat: vi.fn().mockResolvedValue(undefined),
  } as unknown as UseDevicePoolStateReturn
}

function makeActions() {
  return {
    disconnectDialog: ref({
      visible: false,
      serial: '',
      model: '',
      status: '',
      lockedBy: '',
      isBusyOthers: false,
    }),
    networkDialog: ref({ visible: false, loading: false }),
    currentUser: 'u1',
    loadDevices: vi.fn().mockResolvedValue(undefined),
    handleRefresh: vi.fn(),
    openNetworkDialog: vi.fn(),
    handleNetworkConnect: vi.fn(),
    cancelNetworkDialog: vi.fn(),
    handleRowClick: vi.fn(),
    handleLockClick: vi.fn(),
    handleJoinQueue: vi.fn(),
    handleCancelQueue: vi.fn(),
    handleOccupyClick: vi.fn(),
    handleRelease: vi.fn(),
    openDisconnectDialog: vi.fn(),
    handleDisconnectConfirm: vi.fn(),
    cancelDisconnectDialog: vi.fn(),
  } as unknown as UseDeviceActionsReturn
}

function makeHeartbeat() {
  return { heartbeatActive: ref(false), startHeartbeat: vi.fn(), stopHeartbeat: vi.fn() }
}

describe('[P0] DevicePoolView.logic', () => {
  let poolStub: ReturnType<typeof makePool>
  let actionsStub: ReturnType<typeof makeActions>
  let heartbeatStub: ReturnType<typeof makeHeartbeat>

  beforeEach(() => {
    vi.clearAllMocks()
    poolStub = makePool([])
    actionsStub = makeActions()
    heartbeatStub = makeHeartbeat()
    vi.mocked(useDevicePoolState).mockReturnValue(poolStub)
    vi.mocked(useDeviceActions).mockReturnValue(actionsStub)
    vi.mocked(useHeartbeat).mockReturnValue(heartbeatStub)
  })

  it('KPI 统计：按状态聚合 online/busy/offline/total', async () => {
    poolStub.devices.value = [
      makeDevice('S1', 'ONLINE'),
      makeDevice('S2', 'BUSY'),
      makeDevice('S3', 'OFFLINE'),
      makeDevice('S4', 'DISCONNECTED'),
    ]

    const { result } = await mountComposable(() => useDevicePoolView())

    expect(result.kpiStats.value).toEqual({ online: 1, busy: 1, offline: 2, total: 4 })
  })

  it('切换 activeFilter：过滤列表并重置页码', async () => {
    poolStub.devices.value = [
      ...Array.from({ length: 6 }, (_, i) => makeDevice(`O${i + 1}`, 'ONLINE')),
      ...Array.from({ length: 6 }, (_, i) => makeDevice(`F${i + 1}`, 'OFFLINE')),
    ]

    const { result } = await mountComposable(() => useDevicePoolView())

    result.goPage(2)
    expect(result.currentPage.value).toBe(2)

    result.activeFilter.value = 'online'
    await nextTick()

    expect(result.filteredDevices.value).toHaveLength(6)
    expect(result.filteredDevices.value.every((d) => d.status === 'ONLINE')).toBe(true)
    expect(result.currentPage.value).toBe(1)
  })

  it('挂载：调用 loadDevices 与 startHeartbeat', async () => {
    await mountComposable(() => useDevicePoolView())

    expect(actionsStub.loadDevices).toHaveBeenCalledTimes(1)
    expect(heartbeatStub.startHeartbeat).toHaveBeenCalledTimes(1)
  })
})
