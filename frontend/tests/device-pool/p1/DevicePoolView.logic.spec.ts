/**
 * [P1] 建议测 — 设备池页面编排器（mock 三个子 composable，挂载触发 onMounted）
 * 目录：tests/device-pool/p1/
 *
 * useDevicePoolView：设备列表收缩时页码越界收敛、groupedDevices 按状态三分组。
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

describe('[P1] DevicePoolView.logic', () => {
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

  it('设备列表收缩：currentPage 越界收敛到 totalPages', async () => {
    poolStub.devices.value = Array.from({ length: 12 }, (_, i) => makeDevice(`D${i + 1}`))

    const { result } = await mountComposable(() => useDevicePoolView())

    result.goPage(2)
    expect(result.currentPage.value).toBe(2)
    expect(result.totalPages.value).toBe(2)

    poolStub.devices.value = Array.from({ length: 5 }, (_, i) => makeDevice(`D${i + 1}`))
    await nextTick()

    expect(result.filteredDevices.value).toHaveLength(5)
    expect(result.currentPage.value).toBe(1)
    expect(result.pagedDevices.value).toHaveLength(5)
  })

  it('groupedDevices：按状态两分组', async () => {
    poolStub.devices.value = [
      makeDevice('O1', 'ONLINE'),
      makeDevice('O2', 'ONLINE'),
      makeDevice('B1', 'BUSY'),
      makeDevice('B2', 'BUSY'),
    ]

    const { result } = await mountComposable(() => useDevicePoolView())

    const groups = result.groupedDevices.value
    expect(groups.online.map((d) => d.serial)).toEqual(['O1', 'O2'])
    expect(groups.busy.map((d) => d.serial)).toEqual(['B1', 'B2'])
  })
})
