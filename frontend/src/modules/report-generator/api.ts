/**
 * report-generator API & shared helpers — 测试报告模块
 */
import client from '@/shared/api-client'

// ── 执行记录（报告列表）──

export function listRuns(params = {}) {
  return client.get('/reports', { params })
}

export function getCaseBreakdown(result, params = {}) {
  return client.get('/reports/cases', { params: { result, ...params } })
}

// ── 报告详情 ──

export function getRunReport(runId) {
  return client.get(`/reports/run/${encodeURIComponent(runId)}`)
}

// ── 任务视角报告 ──

export function getTaskReport(taskId) {
  return client.get(`/reports/task/${encodeURIComponent(taskId)}`)
}

// ── 文件下载 ──

export function getReportContent(filename) {
  return client.get(`/reports/${encodeURIComponent(filename)}/content`)
}

export function getReportDownloadUrl(filename) {
  return `/api/reports/${encodeURIComponent(filename)}`
}

// ── 共享工具函数 ──

const STATUS_LABEL_MAP = {
  completed: '通过',
  failed: '失败',
  running: '运行中',
  stopped: '已停止',
  pending: '排队中',
}

export function statusLabel(status) {
  return STATUS_LABEL_MAP[status] || status
}

export function statusBadgeClass(status) {
  if (status === 'completed') return 'badge-pass'
  if (status === 'failed') return 'badge-fail'
  if (status === 'running') return 'badge-running'
  return 'badge-stopped'
}

export function iterBadgeClass(result) {
  if (result === 'pass') return 'badge-pass'
  if (result === 'fail' || result === 'stopped') return 'badge-fail'
  return 'badge-stopped'
}

export function formatTime(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    const pad = n => String(n).padStart(2, '0')
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch (_) { return iso }
}
