/** DevicePoolView 逻辑编排器 — 组合子 composable + UI 状态管理 */
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
  /** 状态筛选（下拉控件绑定） */
  activeFilter: Ref<DeviceFilterKey>
  /** 名称搜索关键字：与筛选取交集 */
  searchKey: Ref<string>
  /** 当前是否处于「被收窄」状态（筛选非全部或搜索非空），用于空态文案 */
  hasNarrowing: ComputedRef<boolean>
  // KPIs
  kpiStats: ComputedRef<DeviceKpiStats>
  // filtered + paginated
  filteredDevices: ComputedRef<DeviceRecord[]>
  pagedDevices: ComputedRef<DeviceRecord[]>
  pageSize: Ref<number>
  currentPage: Ref<number>
  totalPages: ComputedRef<number>
  goPage: (p: number) => void
  // dialogs + actions
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
  // helpers
  isRowSelected: (record: DeviceRecord) => boolean
  /** el-table row-class-name：选中行产出共享皮肤认的 `is-selected` */
  rowClassName: (scope: { row: DeviceRecord }) => string
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
  EMPTY_TEXT: typeof EMPTY_TEXT
  SEARCH_PLACEHOLDER: string
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
  const activeFilter = ref<DeviceFilterKey>("all")
  const searchKey = ref("")

  // 5. KPI computed（供筛选 Tab 数量，不再单独展示 Overview）
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

  // 6. Filter：状态筛选 + 名称搜索取交集
  /**
   * 名称搜索匹配：品牌+型号 / 序列号 / 连接地址，任一包含即命中（不区分大小写）。
   * 三者都是界面上可见的设备标识，序列号与地址常用于粘贴定位。
   */
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

  /** 筛选非「全部」或搜索非空 → 空态要说「没有匹配的设备」而不是「还没有设备」 */
  const hasNarrowing = computed(
    () => activeFilter.value !== "all" || searchKey.value.trim().length > 0,
  )

  // 7. Pagination (shared composable, still JS)
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

  /** 有无设备都按每页行数撑开表格高度 */
  const tableMinHeightPx = computed(
    () => TABLE_HEADER_HEIGHT_PX + pageSize.value * TABLE_ROW_HEIGHT_PX,
  )

  const { tableWrapRef, onTablePointerDown } = useTableDragScroll()

  // 8. 筛选或搜索变化 → 回到第 1 页
  watch([activeFilter, searchKey], () => {
    currentPage.value = 1
  })
  watch(filteredDevices, () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  })

  // 9. Row selection helper
  function isRowSelected(record: DeviceRecord): boolean {
    return record && record.serial === pool.selectedSerial.value
  }

  /**
   * 行类名：把选中态交给共享皮肤（唯一类名 `is-selected`），
   * 行底色由 workbench-theme 的 `tr.is-selected > td` 规则承担。
   */
  function rowClassName(scope: { row: DeviceRecord }): string {
    return isRowSelected(scope.row) ? "is-selected" : ""
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
    activeFilter,
    searchKey,
    hasNarrowing,
    // KPIs
    kpiStats,
    // pagination
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
    rowClassName,
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
    EMPTY_TEXT,
    SEARCH_PLACEHOLDER,
  }
}
