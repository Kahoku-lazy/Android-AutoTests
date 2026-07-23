import client from '@/shared/api-client.js'

/** 获取平台概览统计数据 */
export function fetchDashboardStats() {
  return client.get('/dashboard/stats/')
}

/** 获取最近活动日志 */
export function fetchRecentActivities() {
  return client.get('/dashboard/activities/')
}
