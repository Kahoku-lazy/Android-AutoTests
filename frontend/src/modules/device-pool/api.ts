/** Device-Pool API — 设备管理 HTTP 调用（8 端点，DRF {status,data} 信封） */
import client from '@/shared/api-client'
import type { DeviceListResponse, ScanResponse, DeviceOpResponse } from '@/shared/types/device'

export function apiListDevices() {
  return client.get<DeviceListResponse>('/devices')
}

export type DeviceScanBody = {
  target?: string
  pair_port?: string
  pair_code?: string
}

export function apiScanDevices(body?: string | DeviceScanBody) {
  if (typeof body === 'string') {
    return client.post<ScanResponse>('/devices/scan', body ? { target: body } : {})
  }
  const payload: DeviceScanBody = {}
  if (body?.target) payload.target = body.target
  if (body?.pair_port) payload.pair_port = body.pair_port
  if (body?.pair_code) payload.pair_code = body.pair_code
  return client.post<ScanResponse>('/devices/scan', payload)
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
