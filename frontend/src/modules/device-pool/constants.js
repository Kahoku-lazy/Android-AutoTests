/**
 * device-pool 模块常量 — 设备管理
 *
 * 提取自 index.vue，避免魔法值散落。
 */

// ── localStorage key ──
export const STORAGE_KEY_USER_ID = 'dp_user_id'

// ── 筛选 Tabs ──
export const FILTER_TABS = [
  { key: 'all', label: '在线设备' },
  { key: 'busy', label: '使用中' },
]

// ── 表格列定义 ──
export const COLUMNS = [
  { dataIndex: 'serial', title: '序列号', width: 220 },
  { dataIndex: 'model', title: '型号', width: 180 },
  { dataIndex: 'screen', title: '分辨率', width: 130, align: 'center' },
  { dataIndex: 'status', title: '状态', width: 100, align: 'center' },
  { dataIndex: 'connection_type', title: '连接', width: 88, align: 'center' },
  { dataIndex: 'last_seen', title: '最后在线', width: 120 },
  { dataIndex: 'actions', title: '操作', width: 360, fixed: 'right' },
]

// ── 分页配置 ──
export const PAGE_SIZE_OPTIONS = [5, 10, 20]

// ── 心跳轮询间隔 (ms) ──
export const HEARTBEAT_INTERVAL = 30000

// ── 设备状态映射 ──
export const DEVICE_STATUS_MAP = {
  ONLINE: { type: 'success', text: '在线' },
  BUSY: { type: 'warning', text: '使用中' },
  OFFLINE: { type: 'info', text: '离线' },
  DISCONNECTED: { type: 'danger', text: '已断开' },
}

// ── 连接类型标签 ──
export const CONNECTION_TYPE_LABEL = {
  WIFI: '无线 ADB',
  USB: 'USB 有线',
}

// ── Runner/占用前缀（"由自动化占用"判定） ──
export const RUNNER_OCCUPIED_PREFIXES = ['ai_agent', 'runner-', 'task-', 'run-']

// ── 锁默认配置 ──
export const LOCK_DEFAULT_TIMEOUT = 300 // 秒（与后端 api.py acquire_device 默认值一致）
export const LOCK_DEFAULT_MODE = 'occupy'

// ── 时间格式化阈值 ──
export const TIME_FORMAT = {
  MS_DIVISOR: 1000,
  JUST_NOW_SEC: 60,
  HOUR_SEC: 3600,
  DAY_SEC: 86400,
  LABEL_JUST_NOW: '刚刚',
  LABEL_MINUTES_AGO: ' 分钟前',
  LABEL_HOURS_AGO: ' 小时前',
  LABEL_UNKNOWN: '—',
}

// ── 页面 Hero header ──
export const PAGE_HEADER = {
  title: '设备管理',
  subtitle: '扫描、连接、锁定 Android / iOS 设备，管理设备状态与使用队列',
  mark: '📱',
}

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noDevices: '暂无设备',
  noMatch: '没有匹配的设备',
  hintScan: '点击「扫描设备」发现设备',
  hintFilter: '尝试切换筛选条件',
  hintRefresh: '暂无设备，点击「刷新设备」扫描并连接设备',
}

// ── 对话框默认值 ──
export const DEFAULT_DIALOGS = {
  lock: { visible: false, serial: '', model: '' },
  disconnect: { visible: false, serial: '', model: '', status: '', lockedBy: '', isBusyOthers: false },
  network: { visible: false, loading: false },
}

// ── 输入默认值 ──
export const INPUT_DEFAULTS = {
  prefix: 'runner-task-',
  placeholder: '如：runner-task-001、ai_agent',
}

// ── 列表动画配置 ──
export const LIST_ANIMATION = {
  selector:
    '.device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr',
  opacity: [0, 1],
  translateY: [16, 0],
  staggerDelay: 50,
  duration: 350,
  ease: 'outCubic',
}
