/** DevicePoolView 逻辑编排器 — 组合子 composable + UI 状态管理 */
import { ref, computed, watch, onMounted, type Ref, type ComputedRef } from 'vue'
import { useDevicePoolState, type UseDevicePoolStateReturn } from './composables/useDevicePoolState'
import { useDeviceActions, type UseDeviceActionsReturn } from './composables/useDeviceActions'
import { useHeartbeat } from './composables/useHeartbeat'
import { usePagination } from '@/shared/composables/usePagination'
import type {
  DeviceRecord,
  DeviceFilterKey,
  DeviceViewMode,
  DeviceKpiStats,
  DisconnectDialogState,
  NetworkDialogState,
} from '@/shared/types/device'
import {
  PAGE_HEADER,
  FILTER_TABS,
  COLUMNS,
  PAGE_SIZE_OPTIONS,
  CARD_GROUPS,
  EMPTY_TEXT,
} from './constants'
import {
  displayModel,
  connectionLabel,
  deviceAddress,
  formatDateTime,
  formatRelativeTime,
  statusTag,
} from './helpers'

// ── 返回类型接口 ──

export interface DevicePoolViewState {
  // pool state
  devices: Ref<DeviceRecord[]>
  loading: Ref<boolean>
  scanning: Ref<boolean>
  selectedSerial: Ref<string | null>
  error: Ref<string | null>
  // UI state
  viewMode: Ref<DeviceViewMode>
  switchViewMode: (mode: DeviceViewMode) => void
  activeFilter: Ref<DeviceFilterKey>
  // KPIs
  kpiStats: ComputedRef<DeviceKpiStats>
  // filtered + paginated
  filteredDevices: ComputedRef<DeviceRecord[]>
  pagedDevices: ComputedRef<DeviceRecord[]>
  pageSize: Ref<number>
  currentPage: Ref<number>
  totalPages: ComputedRef<number>
  PAGE_SIZE_OPTIONS: number[]
  setPageSize: (n: number) => void
  goPage: (p: number) => void
  // grouped for card view
  groupedDevices: ComputedRef<{
    online: DeviceRecord[]
    busy: DeviceRecord[]
  }>
  // dialogs + actions
  disconnectDialog: Ref<DisconnectDialogState>
  networkDialog: Ref<NetworkDialogState>
  currentUser: string
  handleRefresh: () => Promise<void>
  openNetworkDialog: () => void
  handleNetworkConnect: (opts: { target: string }) => Promise<void>
  cancelNetworkDialog: () => void
  handleRowClick: (record: DeviceRecord) => void
  handleLockClick: (device: DeviceRecord) => Promise<void>
  handleRelease: (serial: string) => Promise<void>
  openDisconnectDialog: (serial: string) => void
  handleDisconnectConfirm: () => Promise<void>
  cancelDisconnectDialog: () => void
  // helpers
  isRowSelected: (record: DeviceRecord) => boolean
  displayModel: typeof displayModel
  connectionLabel: typeof connectionLabel
  deviceAddress: typeof deviceAddress
  formatDateTime: typeof formatDateTime
  formatRelativeTime: typeof formatRelativeTime
  statusTag: typeof statusTag
  // constants
  PAGE_HEADER: typeof PAGE_HEADER
  FILTER_TABS: typeof FILTER_TABS
  COLUMNS: typeof COLUMNS
  CARD_GROUPS: typeof CARD_GROUPS
  EMPTY_TEXT: typeof EMPTY_TEXT
}

// ── Composable ──

export function useDevicePoolView(): DevicePoolViewState {
  // 1. Instantiate shared state (replaces Pinia store)
  const pool = useDevicePoolState()

  // 2. Create heartbeat
  const heartbeat = useHeartbeat()

  // 3. Create actions
  const actions = useDeviceActions(pool)

  // 4. Local UI state
  const viewMode = ref<DeviceViewMode>('table')
  const activeFilter = ref<DeviceFilterKey>('all')

  // 5. KPI computed
  const kpiStats = computed<DeviceKpiStats>(() => {
    const devs = pool.devices.value
    return {
      online: devs.filter((d) => d.status === 'ONLINE').length,
      busy: devs.filter((d) => d.status === 'BUSY').length,
      total: devs.length,
    }
  })

  // 6. Filter
  const filteredDevices = computed<DeviceRecord[]>(() => {
    if (activeFilter.value === 'all') return pool.devices.value
    return pool.devices.value.filter(
      (d) => d.status === activeFilter.value.toUpperCase(),
    )
  })

  // 7. Pagination (shared composable, still JS)
  const {
    pageSize,
    currentPage,
    totalPages,
    pagedItems: pagedDevices,
    setPageSize,
    goPage,
  } = usePagination(filteredDevices, { options: [5, 10, 20] })

  // 8. Watch filter changes → reset page
  watch([activeFilter], () => {
    currentPage.value = 1
  })
  watch(filteredDevices, () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  })

  // 9. Grouped for card view
  const groupedDevices = computed(() => ({
    online: filteredDevices.value.filter((d) => d.status === 'ONLINE'),
    busy: filteredDevices.value.filter((d) => d.status === 'BUSY'),
  }))

  // 10. View mode toggle
  function switchViewMode(mode: DeviceViewMode) {
    viewMode.value = mode
  }

  // 11. Row selection helper
  function isRowSelected(record: DeviceRecord): boolean {
    return record && record.serial === pool.selectedSerial.value
  }

  // 12. Lifecycle
  onMounted(() => {
    actions.loadDevices()
    heartbeat.startHeartbeat(async () => {
      await pool.doHeartbeat()
    })
  })

  return {
    // pool state
    devices: pool.devices,
    loading: pool.loading,
    scanning: pool.scanning,
    selectedSerial: pool.selectedSerial,
    error: pool.error,
    // UI state
    viewMode,
    switchViewMode,
    activeFilter,
    // KPIs
    kpiStats,
    // pagination
    filteredDevices,
    pagedDevices: pagedDevices as ComputedRef<DeviceRecord[]>,
    pageSize,
    currentPage,
    totalPages,
    PAGE_SIZE_OPTIONS,
    setPageSize,
    goPage,
    // grouped
    groupedDevices,
    // dialogs + actions
    disconnectDialog: actions.disconnectDialog,
    networkDialog: actions.networkDialog,
    currentUser: actions.currentUser,
    handleRefresh: actions.handleRefresh,
    openNetworkDialog: actions.openNetworkDialog,
    handleNetworkConnect: actions.handleNetworkConnect,
    cancelNetworkDialog: actions.cancelNetworkDialog,
    handleRowClick: actions.handleRowClick,
    handleLockClick: actions.handleLockClick,
    handleRelease: actions.handleRelease,
    openDisconnectDialog: actions.openDisconnectDialog,
    handleDisconnectConfirm: actions.handleDisconnectConfirm,
    cancelDisconnectDialog: actions.cancelDisconnectDialog,
    // helpers
    isRowSelected,
    displayModel,
    connectionLabel,
    deviceAddress,
    formatDateTime,
    formatRelativeTime,
    statusTag,
    // constants
    PAGE_HEADER,
    FILTER_TABS,
    COLUMNS,
    CARD_GROUPS,
    EMPTY_TEXT,
  }
}
