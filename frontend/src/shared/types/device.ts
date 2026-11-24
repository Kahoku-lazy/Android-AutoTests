export type DeviceStatus = "ONLINE" | "BUSY" | "OFFLINE" | "DISCONNECTED"
export type ConnectionType = "USB" | "WIFI"
export type DeviceFilterKey = "all" | "online" | "busy"

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

export interface DeviceStatusMeta {
  type: "success" | "warning" | "info" | "danger"
  text: string
}

export type DeviceStatusMap = Record<string, DeviceStatusMeta>

export type ConnectionTypeLabelMap = Record<string, string>

export interface FilterTabConfig {
  key: DeviceFilterKey
  label: string

  count?: number
}

export interface ColumnConfig {
  dataIndex: string
  title: string

  icon?: string
  minWidth?: number
  width?: number
  align?: string

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
