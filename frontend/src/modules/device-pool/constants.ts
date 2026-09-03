/** Device-Pool 模块常量 — 纯配置，无函数 */
import type {
  DevicePageHeader,
  FilterTabConfig,
  ColumnConfig,
  DeviceStatusMap,
  ConnectionTypeLabelMap,
  DisconnectDialogState,
  NetworkDialogState,
} from '@/shared/types/device'

// ── 页面 Hero header ──
export const PAGE_HEADER: DevicePageHeader = {
  title: '设备管理',
  subtitle: '扫描、连接、锁定 Android 设备',
  icon: 'smartphone',
  iconGradient: 'linear-gradient(135deg,#95D5B2,#52b788)',
}

// ── 筛选 Tabs（count 由 logic 运行时注入）──
export const FILTER_TABS: FilterTabConfig[] = [
  { key: 'all', label: '全部设备' },
  { key: 'online', label: '在线' },
  { key: 'busy', label: '使用中' },
]

// ── 表格列（定宽，避免 el-table auto + max-content 把列撑爆）──
export const COLUMNS: ColumnConfig[] = [
  { dataIndex: 'device', title: '设备', minWidth: 260, align: 'left', headerAlign: 'center', showOverflowTooltip: false },
  { dataIndex: 'status', title: '状态', width: 150, align: 'center', headerAlign: 'center', showOverflowTooltip: false },
  { dataIndex: 'connection_type', title: '连接', width: 100, align: 'center', headerAlign: 'center', showOverflowTooltip: false },
  { dataIndex: 'lock_status', title: '可见性', width: 120, align: 'center', headerAlign: 'center', showOverflowTooltip: false },
  { dataIndex: 'screen', title: '分辨率', width: 130, align: 'center', headerAlign: 'center' },
  { dataIndex: 'last_seen', title: '活跃', width: 150, align: 'center', headerAlign: 'center', showOverflowTooltip: false },
  { dataIndex: 'actions', title: '操作', width: 220, align: 'center', headerAlign: 'center', showOverflowTooltip: false },
]

/** 表格最小可视行数说明：高度跟随 pageSize（默认 5） */
export const TABLE_HEADER_HEIGHT_PX = 54
export const TABLE_ROW_HEIGHT_PX = 64
/** 表格内容最小宽度，窄屏时可横向滚动 */
export const TABLE_MIN_WIDTH_PX = 1130

// ── 分页配置（默认 5；去掉 20）──
export const PAGE_SIZE_OPTIONS: number[] = [5, 10]
export const DEFAULT_PAGE_SIZE = 5

// ── 心跳轮询间隔 (ms) ──
export const HEARTBEAT_INTERVAL = 30000

// ── 设备状态映射 ──
export const DEVICE_STATUS_MAP: DeviceStatusMap = {
  ONLINE: { type: 'success', text: '在线' },
  BUSY: { type: 'warning', text: '使用中' },
  OFFLINE: { type: 'info', text: '离线 · 不可用' },
  DISCONNECTED: { type: 'danger', text: '已断开 · 不可用' },
}

// ── 连接类型标签 ──
export const CONNECTION_TYPE_LABEL: ConnectionTypeLabelMap = {
  WIFI: '无线 ADB',
  USB: 'USB 有线',
}

// ── Runner/占用前缀 ──
export const RUNNER_OCCUPIED_PREFIXES: string[] = ['ai_agent', 'runner-', 'task-', 'run-']

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noDevices: '还没有可用设备',
  noMatch: '没有匹配的设备',
  hintRefresh: '插入 USB 自动发现，或用局域网连接。也可点「刷新」同步在线状态。',
}

// ── 对话框默认值 ──
export const DEFAULT_DIALOGS = {
  disconnect: { visible: false, serial: '', model: '', status: '', lockedBy: '', isBusyOthers: false } as DisconnectDialogState,
  network: { visible: false, loading: false } as NetworkDialogState,
}

// ── 卡片视图分组配置 ──
export const CARD_GROUPS = [
  { key: 'online' as const, label: '🟢 在线' },
  { key: 'busy' as const, label: '🔴 使用中' },
]

// ── 列表动画配置 ──
export const LIST_ANIMATION = {
  selector: '.device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr',
  opacity: [0, 1] as number[],
  translateY: [16, 0] as number[],
  staggerDelay: 50,
  duration: 350,
  ease: 'outCubic',
}
