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
  TABLE_HEADER_HEIGHT_PX,
  TABLE_ROW_HEIGHT_PX,
  TABLE_MIN_WIDTH_PX,
  DEFAULT_PAGE_SIZE,
} from './constants'
import {
  displayModel,
  connectionLabel,
  deviceAddress,
  formatDateTime,
  formatRelativeTime,
  statusTag,
} from './helpers'
import { useTableDragScroll } from './composables/useTableDragScroll'

// ── 返回类型接口 ──

export interface DevicePoolViewState {
  // pool state
  devices: Ref<DeviceRecord[]>
  loading: Ref<boolean>
  scanning: Ref<boolean>
  selectedSerial: Ref<string | null>
  error: Ref<string | null>
  /** 开发调试：注入模拟设备开关 */
  devMockEnabled: Ref<boolean>
  /** 开发调试：切换模拟设备（60 条） */
  toggleDevMock: (enabled: boolean) => Promise<void>
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
  handleNetworkConnect: (opts: { target: string; pair_port?: string; pair_code?: string }) => Promise<void>
  cancelNetworkDialog: () => void
  handleRowClick: (record: DeviceRecord) => void
  handleLockClick: (device: DeviceRecord) => Promise<void>
  handleRelease: (serial: string) => Promise<void>
  openDisconnectDialog: (serial: string) => void
  handleDisconnectConfirm: () => Promise<void>
  cancelDisconnectDialog: () => void
  // helpers
  isRowSelected: (record: DeviceRecord) => boolean
  deviceRowClassName: (data: { row: DeviceRecord }) => string
  displayModel: typeof displayModel
  connectionLabel: typeof connectionLabel
  deviceAddress: typeof deviceAddress
  formatDateTime: typeof formatDateTime
  formatRelativeTime: typeof formatRelativeTime
  statusTag: typeof statusTag
  // constants
  PAGE_HEADER: typeof PAGE_HEADER
  FILTER_TABS: typeof FILTER_TABS
  filterTabs: ComputedRef<Array<{ key: DeviceFilterKey; label: string; count: number }>>
  COLUMNS: typeof COLUMNS
  CARD_GROUPS: typeof CARD_GROUPS
  EMPTY_TEXT: typeof EMPTY_TEXT
  /** 表格区域最小高度（跟随显示行数：5→5 行高，10→10 行高） */
  tableMinHeightPx: ComputedRef<number>
  tableMinWidthPx: number
  tableWrapRef: Ref<HTMLElement | null>
  onTablePointerDown: (e: PointerEvent) => void
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

  // 5. KPI computed（供筛选 Tab 数量，不再单独展示 Overview）
  const kpiStats = computed<DeviceKpiStats>(() => {
    const devs = pool.devices.value
    return {
      online: devs.filter((d) => d.status === 'ONLINE').length,
      busy: devs.filter((d) => d.status === 'BUSY').length,
      total: devs.length,
    }
  })

  const filterTabs = computed(() =>
    FILTER_TABS.map((tab) => ({
      ...tab,
      count:
        tab.key === 'all'
          ? kpiStats.value.total
          : tab.key === 'online'
            ? kpiStats.value.online
            : kpiStats.value.busy,
    })),
  )

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
  } = usePagination(filteredDevices, {
    pageSize: DEFAULT_PAGE_SIZE,
    options: PAGE_SIZE_OPTIONS,
  })

  /** 有无设备都按当前「显示行数」撑开表格高度 */
  const tableMinHeightPx = computed(
    () => TABLE_HEADER_HEIGHT_PX + pageSize.value * TABLE_ROW_HEIGHT_PX,
  )

  const { tableWrapRef, onTablePointerDown } = useTableDragScroll()

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

  function deviceRowClassName({ row }: { row: DeviceRecord }): string {
    if (row?.status === 'ONLINE') return 'row-online'
    if (row?.status === 'BUSY') return 'row-busy'
    return ''
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
    devMockEnabled: pool.devMockEnabled,
    toggleDevMock: pool.toggleDevMock,
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
    tableMinHeightPx,
    tableMinWidthPx: TABLE_MIN_WIDTH_PX,
    tableWrapRef,
    onTablePointerDown,
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
    deviceRowClassName,
    displayModel,
    connectionLabel,
    deviceAddress,
    formatDateTime,
    formatRelativeTime,
    statusTag,
    // constants
    PAGE_HEADER,
    FILTER_TABS,
    filterTabs,
    COLUMNS,
    CARD_GROUPS,
    EMPTY_TEXT,
  }
}
