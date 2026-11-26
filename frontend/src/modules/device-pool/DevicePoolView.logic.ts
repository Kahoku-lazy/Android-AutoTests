import { ref, computed, watch, onMounted, type Ref, type ComputedRef } from "vue"
import { useDevicePoolState, type UseDevicePoolStateReturn } from "./composables/useDevicePoolState"
import { useDeviceActions, type UseDeviceActionsReturn } from "./composables/useDeviceActions"
import { useHeartbeat } from "./composables/useHeartbeat"
import { usePagination } from "@/shared/composables/usePagination"
import type {
  DeviceRecord,
  DeviceFilterKey,
  DeviceKpiStats,
  DisconnectDialogState,
  NetworkDialogState,
} from "@/shared/types/device"
import {
  PAGE_HEADER,
  FILTER_TABS,
  COLUMNS,
  PAGE_SIZE_OPTIONS,
  EMPTY_TEXT,
  SEARCH_PLACEHOLDER,
  TABLE_HEADER_HEIGHT_PX,
  TABLE_ROW_HEIGHT_PX,
  TABLE_MIN_WIDTH_PX,
  DEFAULT_PAGE_SIZE,
} from "./constants"
import {
  displayModel,
  connectionLabel,
  deviceAddress,
  formatDateTime,
  formatRelativeTime,
  statusTag,
} from "./helpers"
import { useTableDragScroll } from "@/shared/composables/useTableDragScroll"

export interface DevicePoolViewState {
  devices: Ref<DeviceRecord[]>
  loading: Ref<boolean>
  scanning: Ref<boolean>
  selectedSerial: Ref<string | null>
  error: Ref<string | null>

  devMockEnabled: Ref<boolean>

  toggleDevMock: (enabled: boolean) => Promise<void>

  activeFilter: Ref<DeviceFilterKey>

  searchKey: Ref<string>

  hasNarrowing: ComputedRef<boolean>

  kpiStats: ComputedRef<DeviceKpiStats>

  filteredDevices: ComputedRef<DeviceRecord[]>
  pagedDevices: ComputedRef<DeviceRecord[]>
  pageSize: Ref<number>
  currentPage: Ref<number>
  totalPages: ComputedRef<number>
  goPage: (p: number) => void

  disconnectDialog: Ref<DisconnectDialogState>
  networkDialog: Ref<NetworkDialogState>
  currentUser: string
  handleRefresh: () => Promise<void>
  openNetworkDialog: () => void
  handleNetworkConnect: (opts: {
    target: string
    pair_port?: string
    pair_code?: string
  }) => Promise<void>
  cancelNetworkDialog: () => void
  handleRowClick: (record: DeviceRecord) => void
  handleLockClick: (device: DeviceRecord) => Promise<void>
  handleRelease: (serial: string) => Promise<void>
  openDisconnectDialog: (serial: string) => void
  handleDisconnectConfirm: () => Promise<void>
  cancelDisconnectDialog: () => void

  isRowSelected: (record: DeviceRecord) => boolean

  rowClassName: (scope: { row: DeviceRecord }) => string
  displayModel: typeof displayModel
  connectionLabel: typeof connectionLabel
  deviceAddress: typeof deviceAddress
  formatDateTime: typeof formatDateTime
  formatRelativeTime: typeof formatRelativeTime
  statusTag: typeof statusTag

  PAGE_HEADER: typeof PAGE_HEADER
  FILTER_TABS: typeof FILTER_TABS
  filterTabs: ComputedRef<Array<{ key: DeviceFilterKey; label: string; count: number }>>
  COLUMNS: typeof COLUMNS
  EMPTY_TEXT: typeof EMPTY_TEXT
  SEARCH_PLACEHOLDER: string

  tableMinHeightPx: ComputedRef<number>
  tableMinWidthPx: number
  tableWrapRef: Ref<HTMLElement | null>
  onTablePointerDown: (e: PointerEvent) => void
}

export function useDevicePoolView(): DevicePoolViewState {
  const pool = useDevicePoolState()

  const heartbeat = useHeartbeat()

  const actions = useDeviceActions(pool)

  const activeFilter = ref<DeviceFilterKey>("all")
  const searchKey = ref("")

  const kpiStats = computed<DeviceKpiStats>(() => {
    const devs = pool.devices.value
    return {
      online: devs.filter((d) => d.status === "ONLINE").length,
      busy: devs.filter((d) => d.status === "BUSY").length,
      total: devs.length,
    }
  })

  const filterTabs = computed(() =>
    FILTER_TABS.map((tab) => ({
      ...tab,
      count:
        tab.key === "all"
          ? kpiStats.value.total
          : tab.key === "online"
            ? kpiStats.value.online
            : kpiStats.value.busy,
    })),
  )

  function matchSearch(device: DeviceRecord, keyword: string): boolean {
    const k = keyword.trim().toLowerCase()
    if (!k) return true
    const fields = [displayModel(device), device.serial, deviceAddress(device)]
    return fields.some((value) => (value || "").toLowerCase().includes(k))
  }

  const filteredDevices = computed<DeviceRecord[]>(() => {
    const byStatus =
      activeFilter.value === "all"
        ? pool.devices.value
        : pool.devices.value.filter((d) => d.status === activeFilter.value.toUpperCase())
    if (!searchKey.value.trim()) return byStatus
    return byStatus.filter((d) => matchSearch(d, searchKey.value))
  })

  const hasNarrowing = computed(
    () => activeFilter.value !== "all" || searchKey.value.trim().length > 0,
  )

  const {
    pageSize,
    currentPage,
    totalPages,
    pagedItems: pagedDevices,
    goPage,
  } = usePagination(filteredDevices, {
    pageSize: DEFAULT_PAGE_SIZE,
    options: PAGE_SIZE_OPTIONS,
  })

  const tableMinHeightPx = computed(
    () => TABLE_HEADER_HEIGHT_PX + pageSize.value * TABLE_ROW_HEIGHT_PX,
  )

  const { tableWrapRef, onTablePointerDown } = useTableDragScroll()

  watch([activeFilter, searchKey], () => {
    currentPage.value = 1
  })
  watch(filteredDevices, () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  })

  function isRowSelected(record: DeviceRecord): boolean {
    return record && record.serial === pool.selectedSerial.value
  }

  function rowClassName(scope: { row: DeviceRecord }): string {
    return isRowSelected(scope.row) ? "is-selected" : ""
  }

  onMounted(() => {
    actions.loadDevices()
    heartbeat.startHeartbeat(async () => {
      await pool.doHeartbeat()
    })
  })

  return {
    devices: pool.devices,
    loading: pool.loading,
    scanning: pool.scanning,
    selectedSerial: pool.selectedSerial,
    error: pool.error,
    devMockEnabled: pool.devMockEnabled,
    toggleDevMock: pool.toggleDevMock,

    activeFilter,
    searchKey,
    hasNarrowing,

    kpiStats,

    filteredDevices,
    pagedDevices: pagedDevices as ComputedRef<DeviceRecord[]>,
    pageSize,
    currentPage,
    totalPages,
    goPage,
    tableMinHeightPx,
    tableMinWidthPx: TABLE_MIN_WIDTH_PX,
    tableWrapRef,
    onTablePointerDown,

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

    isRowSelected,
    rowClassName,
    displayModel,
    connectionLabel,
    deviceAddress,
    formatDateTime,
    formatRelativeTime,
    statusTag,

    PAGE_HEADER,
    FILTER_TABS,
    filterTabs,
    COLUMNS,
    EMPTY_TEXT,
    SEARCH_PLACEHOLDER,
  }
}
