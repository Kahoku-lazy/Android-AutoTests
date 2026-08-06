/** Dashboard API — 仪表盘统计数据 HTTP 调用 */
import client from '@/shared/api-client'
import type { DashboardRawData, ActivityItem } from '@/shared/types/dashboard'

export function fetchDashboardStats() {
  return client.get<{ ok: boolean; data: DashboardRawData }>('/dashboard/stats/')
}

export function fetchRecentActivities() {
  return client.get<{ ok: boolean; data: ActivityItem[] }>('/dashboard/activities/')
}
