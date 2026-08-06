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
  ok: boolean
  devices?: DeviceRecord[]
  current?: string
  queue_length?: number
  error?: string
}

export interface ScanResponse {
  ok: boolean
  devices?: DeviceRecord[]
  count?: number
  error?: string
}

export interface DeviceOpResponse {
  ok: boolean
  error?: string
  position?: number
}

export interface QueueResponse {
  ok: boolean
  queue?: QueueEntry[]
  count?: number
  error?: string
}
