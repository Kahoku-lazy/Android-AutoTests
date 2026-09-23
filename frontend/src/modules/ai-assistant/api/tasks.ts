/** Task publishing API — TypeScript */
import djangoClient from "@/shared/api-client"
import type { DeviceListResponse } from "@/shared/types/device"
import type {
  TaskDeleteResponse,
  TaskDetailResponse,
  TaskListResponse,
  TaskSubmitResponse,
} from "@/shared/types/ai"

/** 提交任务（multipart：title/goal/可选 attachment 文件/device_*） */
export async function submitTask(payload: FormData): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>("/ai/tasks/submit/", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

/** 任务列表 */
export async function listTasks(): Promise<TaskListResponse> {
  const { data } = await djangoClient.get<TaskListResponse>("/ai/agent-tasks/")
  return data
}

/** 删除任务卡片 */
export async function deleteTask(taskId: number): Promise<TaskDeleteResponse> {
  const { data } = await djangoClient.post<TaskDeleteResponse>(`/ai/agent-tasks/${taskId}/delete/`)
  return data
}

/** 失败任务克隆新建并调度 */
export async function rerunTask(taskId: number): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>(`/ai/agent-tasks/${taskId}/rerun/`)
  return data
}

/** 调试：清空全部任务卡片 */
export async function clearTasks(): Promise<TaskDeleteResponse & { data?: { deleted?: number } }> {
  const { data } = await djangoClient.post<TaskDeleteResponse & { data?: { deleted?: number } }>(
    "/ai/agent-tasks/clear/",
  )
  return data
}

/** 任务详情（过程日志） */
export async function getTask(taskId: number): Promise<TaskDetailResponse> {
  const { data } = await djangoClient.get<TaskDetailResponse>(`/ai/agent-tasks/${taskId}/`)
  return data
}

/** 设备列表（供任务卡片选设备） */
export async function listDevices(): Promise<DeviceListResponse> {
  const { data } = await djangoClient.get<DeviceListResponse>("/devices/")
  return data
}
