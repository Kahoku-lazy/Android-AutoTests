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

// ── 任务持久化 ──

export function listTasks() {
  return client.get('/runner/tasks')
}

export function saveTask(body) {
  return client.post('/runner/tasks/save', body)
}

export function deleteTask(taskId) {
  return client.delete(`/runner/tasks/${taskId}`)
}

// ── 队列管理 ──

export function cancelQueue(clientTaskId, deviceSerial) {
  return client.post('/runner/queue/cancel', {
    client_task_id: clientTaskId,
    device_serial: deviceSerial,
  })
}

// ── 用例定义（跨模块封装，避免组件直接 import case-manager/api）──

export function listDefinitions() {
  return client.get('/cases/definitions')
}

export function listApiDefinitions() {
  return client.get('/cases/api-definitions')
}

export function listWebDefinitions() {
  return client.get('/cases/web-definitions')
}

// ── 设备列表（跨模块）──

export function listDevices() {
  return client.get('/devices')
}
