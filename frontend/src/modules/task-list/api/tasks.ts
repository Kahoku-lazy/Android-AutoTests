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
  const { data } = await djangoClient.post<TaskSubmitResponse>("/tasks/submit/", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

/** 任务列表 */
export async function listTasks(): Promise<TaskListResponse> {
  const { data } = await djangoClient.get<TaskListResponse>("/tasks/")
  return data
}

/** 删除任务卡片 */
export async function deleteTask(taskId: number): Promise<TaskDeleteResponse> {
  const { data } = await djangoClient.post<TaskDeleteResponse>(`/tasks/${taskId}/delete/`)
  return data
}

/** 关闭运行中的 SOP */
export async function cancelTask(taskId: number): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>(`/tasks/${taskId}/cancel/`)
  return data
}

/** 失败任务克隆新建并调度 */
export async function rerunTask(taskId: number): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>(`/tasks/${taskId}/rerun/`)
  return data
}

/** 调试：清空全部任务卡片 */
export async function clearTasks(): Promise<TaskDeleteResponse & { data?: { deleted?: number } }> {
  const { data } = await djangoClient.post<TaskDeleteResponse & { data?: { deleted?: number } }>(
    "/tasks/clear/",
  )
  return data
}

/** 任务详情（过程日志） */
export async function getTask(taskId: number): Promise<TaskDetailResponse> {
  const { data } = await djangoClient.get<TaskDetailResponse>(`/tasks/${taskId}/`)
  return data
}

/** 设备列表（供任务卡片选设备） */
export async function listDevices(): Promise<DeviceListResponse> {
  const { data } = await djangoClient.get<DeviceListResponse>("/devices/")
  return data
}
/** 任务附件/图片上传（multipart） */
export async function uploadTaskFile(
  formData: FormData,
): Promise<{ status: boolean; data?: unknown }> {
  const { data } = await djangoClient.post<{ status: boolean; data?: unknown }>(
    "/tasks/upload-file/",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  )
  return data
}

/** 任务事件流程报告（详情页） */
export async function getTaskReport(
  taskId: number,
): Promise<{ status: boolean; message?: string; [key: string]: unknown }> {
  const { data } = await djangoClient.get(`/tasks/${taskId}/report/`)
  return data
}
