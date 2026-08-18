/** Device-Pool API — 设备管理 HTTP 调用（8 端点，DRF {status,data} 信封） */
import client from '@/shared/api-client'
import type { DeviceListResponse, ScanResponse, DeviceOpResponse } from '@/shared/types/device'

export function apiListDevices() {
  return client.get<DeviceListResponse>('/devices')
}

export function apiScanDevices(target?: string) {
  return client.post<ScanResponse>('/devices/scan', target ? { target } : {})
}

export function apiConnectDevice(serial: string, { activate = true }: { activate?: boolean } = {}) {
  return client.post<DeviceOpResponse>(`/devices/${serial}`, { activate })
}

export function apiActivate(serial: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/activate`)
}

export function apiLockDevice(serial: string, locked: boolean) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/lock`, { locked })
}

export function apiReleaseDevice(serial: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/release`)
}

export function apiDisconnect(serial: string) {
  return client.post<DeviceOpResponse>(`/devices/${serial}/disconnect`)
}

export function apiHeartbeat() {
  return client.get('/devices/heartbeat')
}
