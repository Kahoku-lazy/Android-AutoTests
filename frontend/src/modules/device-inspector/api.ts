/** device-inspector API client functions — 快照化端点 + 分层查询 + 设备列表 */
import client from "@/shared/api-client"

// ── Capture & snapshots ──

export function apiCapture(serial, method) {
  return client.post("/inspector/capture/", { serial, method })
}
export function apiGetSnapshots(offset = 0, limit = 100) {
  return client.get("/inspector/snapshots/", { params: { offset, limit } })
}
/** 分层查询：分组摘要 + 全量元素条目（含被展示裁剪丢弃的），支持服务端筛减兜底 */
export function apiGetLayers(id, params = {}) {
  return client.get(`/inspector/snapshots/${id}/layers/`, { params })
}
export function apiDeleteSnapshot(id) {
  return client.delete(`/inspector/snapshots/${id}/delete/`)
}
/** 一键清空本人的全部历史快照（返回删除条数）；只清自己，媒体按引用判定保留 */
export function apiClearSnapshots() {
  return client.delete("/inspector/snapshots/clear/")
}

// ── Save to element locator ──

export function apiSaveToElements(id, payload) {
  return client.post(`/inspector/snapshots/${id}/save-elements/`, payload)
}

// ── Device integration (device-pool) ──

export function apiGetDevices() {
  return client.get("/devices/")
}
