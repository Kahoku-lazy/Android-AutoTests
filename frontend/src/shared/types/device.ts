/** Device-Pool 模块共享类型 — 设备管理 */

// ── 枚举类型 ──

export type DeviceStatus = 'ONLINE' | 'BUSY' | 'OFFLINE' | 'DISCONNECTED'
export type ConnectionType = 'USB' | 'WIFI'
export type DeviceFilterKey = 'all' | 'online' | 'busy' | 'offline'
export type DeviceViewMode = 'table' | 'cards'

// ── 核心数据 ──

export interface DeviceRecord {
  serial: string
  model?: string
  brand?: string
  name?: string
  screen?: string
  status: DeviceStatus
  connection_type: ConnectionType
  locked_by?: string
  occupied_by?: string
  last_seen: string
}

export interface QueueEntry {
  user_id: string
  serial: string
  waited_seconds?: number
}

// ── UI 状态 ──

export interface DeviceKpiStats {
  online: number
  busy: number
  offline: number
  total: number
}

export interface DisconnectDialogState {
  visible: boolean
  serial: string
  model: string
  status: string
  lockedBy: string
  isBusyOthers: boolean
}

export interface NetworkDialogState {
  visible: boolean
  loading: boolean
}

// ── 显示辅助 ──

export interface DeviceStatusMeta {
  type: 'success' | 'warning' | 'info' | 'danger'
  text: string
}

/** 设备状态 → 展示 meta 映射表 */
export type DeviceStatusMap = Record<string, DeviceStatusMeta>

/** 连接类型 → 中文标签映射表 */
export type ConnectionTypeLabelMap = Record<string, string>

// ── 配置类型 ──

export interface FilterTabConfig {
  key: DeviceFilterKey
  label: string
}

export interface ColumnConfig {
  dataIndex: string
  title: string
  minWidth?: number
  width?: number
  align?: string
  fixed?: string
}

export interface DevicePageHeader {
  title: string
  subtitle: string
  icon: string
  iconGradient: string
}

// ── API 响应 ──

export interface DeviceListResponse {
  status: boolean
  devices?: DeviceRecord[]
  current?: string
  queue_length?: number
  message?: string
}

export interface ScanResponse {
  status: boolean
  devices?: DeviceRecord[]
  count?: number
  message?: string
}

export interface DeviceOpResponse {
  status: boolean
  message?: string
  position?: number
}

export interface QueueResponse {
  status: boolean
  queue?: QueueEntry[]
  count?: number
  message?: string
}
