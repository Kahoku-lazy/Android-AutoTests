/** Task publishing API — TypeScript */
import djangoClient from '@/shared/api-client'
import type { DeviceListResponse } from '@/shared/types/device'
import type {
  TaskListResponse,
  TaskSubmitPayload,
  TaskSubmitResponse,
} from '@/shared/types/ai'

/** 提交任务 */
export async function submitTask(payload: TaskSubmitPayload): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>('/ai/tasks/submit', payload)
  return data
}

/** 任务列表 */
export async function listTasks(): Promise<TaskListResponse> {
  const { data } = await djangoClient.get<TaskListResponse>('/ai/agent-tasks')
  return data
}

/** 设备列表（供任务卡片选设备） */
export async function listDevices(): Promise<DeviceListResponse> {
  const { data } = await djangoClient.get<DeviceListResponse>('/devices')
  return data
}
