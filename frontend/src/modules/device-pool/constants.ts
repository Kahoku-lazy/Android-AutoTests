import type {
  DevicePageHeader,
  FilterTabConfig,
  ColumnConfig,
  DeviceStatusMap,
  ConnectionTypeLabelMap,
  DisconnectDialogState,
  NetworkDialogState,
} from "@/shared/types/device"

export const PAGE_HEADER: DevicePageHeader = {
  title: "设备管理",
  subtitle: "扫描、连接、锁定 Android 设备",
  icon: "smartphone",
  iconGradient: "linear-gradient(135deg,#95D5B2,#52b788)",
}

export const FILTER_TABS: FilterTabConfig[] = [
  { key: "all", label: "全部设备" },
  { key: "online", label: "在线" },
  { key: "busy", label: "使用中" },
]

export const COLUMNS: ColumnConfig[] = [
  {
    dataIndex: "device",
    title: "设备",
    icon: "🖥",
    minWidth: 220,
    align: "left",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    dataIndex: "status",
    title: "状态",
    icon: "🟢",
    minWidth: 120,
    align: "center",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    dataIndex: "connection_type",
    title: "连接",
    icon: "🔌",
    minWidth: 90,
    align: "center",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    dataIndex: "lock_status",
    title: "可见性",
    icon: "👁",
    minWidth: 110,
    align: "center",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    dataIndex: "screen",
    title: "分辨率",
    icon: "🖼",
    minWidth: 120,
    align: "center",
    headerAlign: "center",
  },
  {
    dataIndex: "last_seen",
    title: "活跃",
    icon: "⏱",
    minWidth: 140,
    align: "center",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    dataIndex: "actions",
    title: "操作",
    icon: "💬",
    minWidth: 180,
    align: "center",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
]

export const TABLE_HEADER_HEIGHT_PX = 54
export const TABLE_ROW_HEIGHT_PX = 64

export const TABLE_MIN_WIDTH_PX = 980

export const PAGE_SIZE_OPTIONS: number[] = [7]
export const DEFAULT_PAGE_SIZE = 7

export const HEARTBEAT_INTERVAL = 30000

export const DEVICE_STATUS_MAP: DeviceStatusMap = {
  ONLINE: { type: "success", text: "在线" },
  BUSY: { type: "warning", text: "使用中" },
  OFFLINE: { type: "info", text: "离线 · 不可用" },
  DISCONNECTED: { type: "danger", text: "已断开 · 不可用" },
}

export const CONNECTION_TYPE_LABEL: ConnectionTypeLabelMap = {
  WIFI: "无线 ADB",
  USB: "USB 有线",
}

export const EMPTY_TEXT = {
  noDevices: "还没有可用设备",
  noMatch: "没有匹配的设备",
  hintRefresh: "插入 USB 自动发现，或用局域网连接。也可点「刷新」同步在线状态。",
  hintClearSearch: "换个关键字，或清空搜索条件。",
}

export const SEARCH_PLACEHOLDER = "搜索设备名称 / 序列号 / 地址"

export const IPV4_RE = /^((25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[01]?\d?\d)$/
export const ADB_PORT_MIN = 1024
export const ADB_PORT_MAX = 65535

export const DEFAULT_DIALOGS = {
  disconnect: {
    visible: false,
    serial: "",
    model: "",
    status: "",
    lockedBy: "",
    isBusyOthers: false,
  } as DisconnectDialogState,
  network: { visible: false, loading: false } as NetworkDialogState,
}

export const LIST_ANIMATION = {
  selector: ".device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr",
  opacity: [0, 1] as number[],
  translateY: [16, 0] as number[],
  staggerDelay: 50,
  duration: 350,
  ease: "outCubic",
}
