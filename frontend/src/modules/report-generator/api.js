/**
 * report-generator API — 测试报告模块
 */
import client from '@/shared/api-client.js'

// ── 报告 ──

export function listReports() {
  return client.get('/reports')
}

export function getReportContent(filename) {
  return client.get(`/reports/${encodeURIComponent(filename)}/content`)
}

export function getReportDownloadUrl(filename) {
  return `/api/reports/${encodeURIComponent(filename)}`
}

// ── 执行历史（跨模块）──

export function listRuns() {
  return client.get('/runner/runs')
}
