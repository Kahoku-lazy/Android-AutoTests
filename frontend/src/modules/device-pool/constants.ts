/** Device-Pool 模块常量 — 纯配置，无函数 */
import type {
  DevicePageHeader,
  FilterTabConfig,
  ColumnConfig,
  DeviceStatusMap,
  ConnectionTypeLabelMap,
  DisconnectDialogState,
  NetworkDialogState,
} from "@/shared/types/device"

// ── 页面 Hero header ──
export const PAGE_HEADER: DevicePageHeader = {
  title: "设备管理",
  subtitle: "扫描、连接、锁定 Android 设备",
  icon: "smartphone",
  iconGradient: "linear-gradient(135deg,#95D5B2,#52b788)",
}

// ── 筛选 Tabs（count 由 logic 运行时注入）──
export const FILTER_TABS: FilterTabConfig[] = [
  { key: "all", label: "全部设备" },
  { key: "online", label: "在线" },
  { key: "busy", label: "使用中" },
]

// ── 表格列（全列 minWidth：宽屏按比例均摊，避免只拉大「设备」列）──
// icon 只进表头（配合 #header-<prop> 插槽渲染），title 保持纯文字：
// 表头 tooltip 与读屏仍只读列名，数据单元格保持无图标、可等宽扫读。
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

/** 表格最小可视行数说明：高度跟随 pageSize（默认 5） */
export const TABLE_HEADER_HEIGHT_PX = 54
export const TABLE_ROW_HEIGHT_PX = 64
/** 表格内容最小宽度（≈ 各列 minWidth 之和） */
export const TABLE_MIN_WIDTH_PX = 980

// ── 分页配置（表格固定每页 7 行；行数选择器已下线，选项集仍是唯一真相源）──
export const PAGE_SIZE_OPTIONS: number[] = [7]
export const DEFAULT_PAGE_SIZE = 7

// ── 心跳轮询间隔 (ms) ──
export const HEARTBEAT_INTERVAL = 30000

// ── 设备状态映射 ──
export const DEVICE_STATUS_MAP: DeviceStatusMap = {
  ONLINE: { type: "success", text: "在线" },
  BUSY: { type: "warning", text: "使用中" },
  OFFLINE: { type: "info", text: "离线 · 不可用" },
  DISCONNECTED: { type: "danger", text: "已断开 · 不可用" },
}

// ── 连接类型标签 ──
export const CONNECTION_TYPE_LABEL: ConnectionTypeLabelMap = {
  WIFI: "无线 ADB",
  USB: "USB 有线",
}

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noDevices: "还没有可用设备",
  noMatch: "没有匹配的设备",
  hintRefresh: "插入 USB 自动发现，或用局域网连接。也可点「刷新」同步在线状态。",
  hintClearSearch: "换个关键字，或清空搜索条件。",
}

// ── 搜索框 ──
export const SEARCH_PLACEHOLDER = "搜索设备名称 / 序列号 / 地址"

// ── 对话框默认值 ──
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

// ── 列表动画配置 ──
export const LIST_ANIMATION = {
  selector: ".device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr",
  opacity: [0, 1] as number[],
  translateY: [16, 0] as number[],
  staggerDelay: 50,
  duration: 350,
  ease: "outCubic",
}
