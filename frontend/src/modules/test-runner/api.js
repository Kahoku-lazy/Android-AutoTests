/**
 * test-runner API — 测试执行模块
 */
import client from '@/shared/api-client.js'

// ── 测试执行 ──

export function startRun(body) {
  return client.post('/runner/run', body)
}

export function stopRun(runId) {
  return client.post(`/runner/run/${runId}/stop`)
}

export function getActiveRuns() {
  return client.get('/runner/active')
}

// ── 用例定义（跨模块）──

export function listDefinitions() {
  return client.get('/cases/definitions')
}

// ── 设备列表（跨模块）──

export function listDevices() {
  return client.get('/devices')
}
