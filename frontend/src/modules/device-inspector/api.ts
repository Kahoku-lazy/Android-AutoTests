/** device-inspector API client functions — v1.7 快照化 6 端点 + 设备列表 */
import client from '@/shared/api-client'

// ── Capture & snapshots ──

export function apiCapture(serial, method) {
  return client.post('/inspector/capture', { serial, method })
}
export function apiGetSnapshots(offset = 0, limit = 100) {
  return client.get('/inspector/snapshots', { params: { offset, limit } })
}
export function apiGetSnapshot(id) {
  return client.get(`/inspector/snapshots/${id}`)
}
export function apiDeleteSnapshot(id) {
  return client.delete(`/inspector/snapshots/${id}/delete`)
}
export function apiAnalyzeSnapshot(id) {
  return client.get(`/inspector/snapshots/${id}/analyze`)
}

// ── Save to element locator ──

export function apiSaveToElements(id, payload) {
  return client.post(`/inspector/snapshots/${id}/save-elements`, payload)
}

// ── Saved page view (read-only) ──

export function apiGetPageView(pageId) {
  return client.get(`/inspector/pages/${pageId}`)
}

// ── Device integration (device-pool) ──

export function apiGetDevices() {
  return client.get('/devices')
}
