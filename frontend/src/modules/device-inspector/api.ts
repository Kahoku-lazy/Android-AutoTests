/** device-inspector API client functions */
import client from '@/shared/api-client'

// ── Element dump ──

export function apiDump()         { return client.post('/inspector/dump', {}) }
export function apiOcr()          { return client.post('/inspector/ocr', {}) }

// ── Device integration ──

export function apiGetDevices()           { return client.get('/devices') }
export function apiActivateDevice(s)      { return client.post(`/devices/${s}/activate`) }
export function apiGetDeviceInfo()        { return client.get('/inspector/device-info') }
export function apiGetScreenshot()        { return client.get('/inspector/screenshot') }

// ── Observe-mode connect/disconnect (manual device control) ──

export function apiConnectObserve(serial) {
  return client.post(`/devices/${serial}`, { activate: true, mode: 'observe' })
}
export function apiDisconnectObserve(serial) {
  return client.post(`/devices/${serial}/disconnect-observe`)
}
