/** Device-Pool API — 设备管理 HTTP 调用（12 endpoints） */
import client from '@/shared/api-client'
import type { DeviceListResponse, ScanResponse, DeviceOpResponse, QueueResponse } from '@/shared/types/device'

export function apiListDevices() {
  return client.get<DeviceListResponse>('/devices')
}

export function apiScanDevices(target?: string) {
  return client.post<ScanResponse>('/devices/scan', target ? { target } : {})
}

export function apiConnectDevice(serial: string, { activate = true, userId, timeout }: {
  activate?: boolean; userId?: string; timeout?: number
} = {}) {
  return client.post<DeviceOpResponse>(`/devices/${serial}`, {
    activate,
    user_id: userId || '',
    timeout: timeout || 300,
  })
}

export function apiActivate(serial: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/activate`)
}

export function apiLockDevice(serial: string, userId: string, timeout = 300, type = 'user') {
  return client.post<DeviceOpResponse>(`/devices/${serial}/lock`, {
    user_id: userId,
    timeout,
    type,
  })
}

export function apiReleaseDevice(serial: string, { userId, reason = 'manual', unlock = false, force = false }: {
  userId?: string; reason?: string; unlock?: boolean; force?: boolean
} = {}) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/release`, {
    user_id: userId || '',
    reason,
    unlock,
    force,
  })
}

export function apiDisconnect(serial: string, { force = false, reason = '', userId, isAdmin }: {
  force?: boolean; reason?: string; userId?: string; isAdmin?: boolean
} = {}) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/disconnect`, {
    force,
    reason,
    user_id: userId || '',
    is_admin: isAdmin || false,
  })
}

export function apiGetQueue() {
  return client.get<QueueResponse>('/devices/queue')
}

export function apiJoinQueue(serial: string, userId: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/queue`, { user_id: userId })
}

export function apiLeaveQueue(serial: string, userId: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/queue/leave`, { user_id: userId || '' })
}

export function apiHeartbeat() {
  return client.get('/devices/heartbeat')
}
