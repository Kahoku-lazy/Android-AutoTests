/**
 * 跨模块共享 API 端点函数
 *
 * 统一命名规范：
 *   fetch*  = GET（只读查询）
 *   create* = POST 创建
 *   update* = POST/PUT 更新
 *   remove* = POST/DELETE 删除
 *
 * 使用方式：模块 api.js 中直接 re-export 或直接调用
 *   import { fetchDevices } from '@/shared/endpoints.js'
 */

import client from './api-client.js'

// ═══════════════════════════════════════════════════════════════
// device-pool — 设备
// ═══════════════════════════════════════════════════════════════

/** 获取所有设备列表 */
export function fetchDevices() {
  return client.get('/devices')
}

/** 获取当前用户锁定的设备 */
export function fetchCurrentDevice() {
  return client.get('/devices/current')
}

/** 扫描 ADB 设备 */
export function scanDevices(target) {
  return client.post('/devices/scan', target ? { target } : {})
}

/** 连接设备 */
export function connectDevice(serial, opts = {}) {
  return client.post(`/devices/${serial}`, opts)
}

/** 激活设备 */
export function activateDevice(serial) {
  return client.post(`/devices/${serial}/activate`)
}

/** 断开设备 */
export function disconnectDevice(serial, opts = {}) {
  return client.post(`/devices/${serial}/disconnect`, opts)
}

/** 锁定设备 */
export function lockDevice(serial, userId, timeout = 300) {
  return client.post(`/devices/${serial}/lock`, { user_id: userId, timeout })
}

/** 释放设备 */
export function releaseDevice(serial, userId, reason = 'manual') {
  return client.post(`/devices/${serial}/release`, { user_id: userId, reason })
}

/** 获取设备队列 */
export function fetchDeviceQueue() {
  return client.get('/devices/queue')
}

/** 加入设备队列 */
export function joinDeviceQueue(serial, userId) {
  return client.post(`/devices/${serial}/queue`, { user_id: userId })
}

/** 离开设备队列 */
export function leaveDeviceQueue(serial, userId) {
  return client.post(`/devices/${serial}/queue/leave`, { user_id: userId || '' })
}

// ═══════════════════════════════════════════════════════════════
// element-locator — UI 元素/页面
// ═══════════════════════════════════════════════════════════════

/** 获取所有已保存页面 */
export function fetchPages() {
  return client.get('/elements/pages')
}

/** 获取页面下的元素列表 */
export function fetchPageElements(pageId, filter) {
  return client.get(`/elements/pages/${pageId}/items`, { params: { filter } })
}

/** 获取设备信息 */
export function fetchDeviceInfo() {
  return client.get('/elements/device-info')
}

/** 获取当前截图 */
export function fetchScreenshot() {
  return client.get('/elements/screenshot')
}

// ═══════════════════════════════════════════════════════════════
// case-manager — 测试用例
// ═══════════════════════════════════════════════════════════════

/** 获取用例定义列表 */
export function fetchDefinitions(params) {
  return client.get('/cases/definitions', { params })
}

/** 获取单个用例详情 */
export function fetchDefinition(id) {
  return client.get(`/cases/definitions/${id}`)
}

/** 获取用例目录树 */
export function fetchDirectories() {
  return client.get('/cases/directories')
}

// ═══════════════════════════════════════════════════════════════
// test-runner — 执行引擎
// ═══════════════════════════════════════════════════════════════

/** 获取活跃执行列表 */
export function fetchActiveRuns() {
  return client.get('/runner/active')
}

/** 启动测试执行 */
export function startRun(body) {
  return client.post('/runner/run', body)
}

/** 停止执行 */
export function stopRun(runId) {
  return client.post(`/runner/run/${runId}/stop`)
}

/** 获取执行历史 */
export function fetchRuns(params) {
  return client.get('/runner/runs', { params })
}

// ═══════════════════════════════════════════════════════════════
// report-generator — 报告
// ═══════════════════════════════════════════════════════════════

/** 获取报告列表 */
export function fetchReports(params) {
  return client.get('/reports', { params })
}
