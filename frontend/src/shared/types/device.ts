/** Device-Pool 模块共享类型 — 设备管理 */

// ── 枚举类型 ──

export type DeviceStatus = 'ONLINE' | 'BUSY' | 'OFFLINE' | 'DISCONNECTED'
export type ConnectionType = 'USB' | 'WIFI'
export type DeviceFilterKey = 'all' | 'online' | 'busy'
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
  connection_addr?: string
  locked?: boolean
  locked_by?: string
  occupied_by?: string
  connected_at?: string
  added_by?: string
  last_seen: string
}

// ── UI 状态 ──

export interface DeviceKpiStats {
  online: number
  busy: number
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
  /** 可选数量角标（如全部 / 在线 / 使用中） */
  count?: number
}

export interface ColumnConfig {
  dataIndex: string
  title: string
  minWidth?: number
  width?: number
  align?: string
  /** 表头对齐；缺省跟 align */
  headerAlign?: string
  fixed?: string
  showOverflowTooltip?: boolean
}

export interface DevicePageHeader {
  title: string
  subtitle: string
  icon: string
  iconGradient: string
}

// ── API 响应（DRF 信封 {status, data}） ──

export interface DeviceListResponse {
  status: boolean
  data?: { devices: DeviceRecord[]; current?: string }
  message?: string
}

export interface ScanResponse {
  status: boolean
  data?: { devices?: DeviceRecord[]; count?: number; newly_added?: number }
  message?: string
}

export interface DeviceOpResponse {
  status: boolean
  data?: { [key: string]: unknown }
  message?: string
}
