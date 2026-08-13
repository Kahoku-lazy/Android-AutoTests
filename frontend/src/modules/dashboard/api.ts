/** Dashboard API — 仪表盘统计数据 HTTP 调用 */
import client, { type DjangoResponse } from '@/shared/api-client'
import type { DashboardRawData, ActivityItem } from '@/shared/types/dashboard'

export function fetchDashboardStats() {
  return client.get<DjangoResponse<DashboardRawData>>('/dashboard/stats/')
}

export function fetchRecentActivities() {
  return client.get<DjangoResponse<ActivityItem[]>>('/dashboard/activities/')
}
