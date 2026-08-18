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
  subtitle: '扫描、连接、锁定 Android 设备，管理设备状态与使用队列',
  icon: 'smartphone',
  iconGradient: 'linear-gradient(135deg,#95D5B2,#52b788)',
}

// ── 筛选 Tabs ──
export const FILTER_TABS: FilterTabConfig[] = [
  { key: 'all', label: '全部设备' },
  { key: 'online', label: '在线' },
  { key: 'busy', label: '使用中' },
]

// ── 表格列定义 ──
export const COLUMNS: ColumnConfig[] = [
  { dataIndex: 'adb_addr', title: '设备地址', minWidth: 180 },
  { dataIndex: 'serial', title: '序列号', minWidth: 200 },
  { dataIndex: 'model', title: '型号', minWidth: 120 },
  { dataIndex: 'screen', title: '分辨率', minWidth: 110, align: 'center' },
  { dataIndex: 'status', title: '状态', minWidth: 160, align: 'center' },
  { dataIndex: 'connection_type', title: '连接', minWidth: 180, align: 'center' },
  { dataIndex: 'lock_status', title: '锁定', minWidth: 100, align: 'center' },
  { dataIndex: 'connected_at', title: '设备连接时间点', minWidth: 150 },
  { dataIndex: 'last_seen', title: '最后在线', minWidth: 110 },
  { dataIndex: 'actions', title: '操作', width: 220, fixed: 'right' },
]

// ── 分页配置 ──
export const PAGE_SIZE_OPTIONS: number[] = [5, 10, 20]

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
  noDevices: '暂无设备',
  noMatch: '没有匹配的设备',
  hintRefresh: '暂无设备，点击「刷新设备」扫描并连接设备',
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
