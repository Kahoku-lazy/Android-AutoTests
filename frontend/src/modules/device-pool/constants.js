/**
 * device-pool 模块常量 — 设备管理
 *
 * 提取自 index.vue 各组件，统一管理避免魔法值散落。
 * 以下常量全部由 index.vue 及子组件 import 使用。
 */

// ── 页面 Hero header ──
export const PAGE_HEADER = {
  title: '设备管理',
  subtitle: '扫描、连接、锁定 Android 设备，管理设备状态与使用队列',
  icon: 'smartphone',
  iconGradient: 'linear-gradient(135deg,#95D5B2,#52b788)',
}

// ── 筛选 Tabs（与 index.vue filterAppTabs 对齐） ──
export const FILTER_TABS = [
  { key: 'all', label: '全部设备' },
  { key: 'online', label: '在线' },
  { key: 'busy', label: '使用中' },
  { key: 'offline', label: '离线' },
]

// ── 表格列定义（与 index.vue 实际渲染对齐） ──
export const COLUMNS = [
  { dataIndex: 'serial', title: '序列号', minWidth: 200 },
  { dataIndex: 'model', title: '型号', minWidth: 120 },
  { dataIndex: 'screen', title: '分辨率', minWidth: 110, align: 'center' },
  { dataIndex: 'status', title: '状态', minWidth: 160, align: 'center' },
  { dataIndex: 'connection_type', title: '连接', minWidth: 90, align: 'center' },
  { dataIndex: 'lock_status', title: '锁定', minWidth: 100, align: 'center' },
  { dataIndex: 'last_seen', title: '最后在线', minWidth: 110 },
  { dataIndex: 'actions', title: '操作', width: 220, fixed: 'right' },
]

// ── 分页配置 ──
export const PAGE_SIZE_OPTIONS = [5, 10, 20]

// ── 心跳轮询间隔 (ms) ──
export const HEARTBEAT_INTERVAL = 30000

// ── 设备状态映射 ──
export const DEVICE_STATUS_MAP = {
  ONLINE: { type: 'success', text: '在线' },
  BUSY: { type: 'warning', text: '使用中' },
  OFFLINE: { type: 'info', text: '离线 · 不可用' },
  DISCONNECTED: { type: 'danger', text: '已断开 · 不可用' },
}

// ── 连接类型标签 ──
export const CONNECTION_TYPE_LABEL = {
  WIFI: '无线 ADB',
  USB: 'USB 有线',
}

// ── Runner/占用前缀（"由自动化占用"判定）—— 三处统一引用此处 ──
export const RUNNER_OCCUPIED_PREFIXES = ['ai_agent', 'runner-', 'task-', 'run-']

// ── 时间格式化 ──
export function formatRelativeTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

// ── 辅助格式化 ──
export function displayModel(device) {
  const parts = []
  if (device.brand) parts.push(device.brand)
  if (device.model) parts.push(device.model)
  return parts.length ? parts.join(' ') : '—'
}

export function connectionLabel(type) {
  return CONNECTION_TYPE_LABEL[type] || type || '—'
}

export function statusTag(status) {
  return DEVICE_STATUS_MAP[status] || { type: 'info', text: status }
}

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noDevices: '暂无设备',
  noMatch: '没有匹配的设备',
  hintRefresh: '暂无设备，点击「刷新设备」扫描并连接设备',
}

// ── 对话框默认值 ──
export const DEFAULT_DIALOGS = {
  disconnect: { visible: false, serial: '', model: '', status: '', lockedBy: '', isBusyOthers: false },
  network: { visible: false, loading: false },
}

// ── 列表动画配置 ──
export const LIST_ANIMATION = {
  selector: '.device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr',
  opacity: [0, 1],
  translateY: [16, 0],
  staggerDelay: 50,
  duration: 350,
  ease: 'outCubic',
}
