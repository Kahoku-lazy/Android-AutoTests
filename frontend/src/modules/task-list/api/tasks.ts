import djangoClient from "@/shared/api-client"
import type {
  TaskDeleteResponse,
  TaskDetailResponse,
  TaskListResponse,
  TaskStatsResponse,
  TaskSubmitResponse,
} from "@/shared/types/ai"

export async function fetchTaskReport(run: string, name: string): Promise<string> {
  const { data } = await djangoClient.get<{ status: boolean; data?: { content?: string } }>(
    `/ai/agent-reports/${encodeURIComponent(run)}/${encodeURIComponent(name)}/`,
  )
  return data.data?.content || ""
}

export async function listTasks(params?: {
  workflow_id?: number
  status?: string
}): Promise<TaskListResponse> {
  const { data } = await djangoClient.get<TaskListResponse>("/tasks/", { params })
  return data
}

export async function getTaskStats(): Promise<TaskStatsResponse> {
  const { data } = await djangoClient.get<TaskStatsResponse>("/tasks/stats/")
  return data
}

export async function deleteTask(taskId: number): Promise<TaskDeleteResponse> {
  const { data } = await djangoClient.post<TaskDeleteResponse>(`/tasks/${taskId}/delete/`)
  return data
}

export async function cancelTask(taskId: number): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>(`/tasks/${taskId}/cancel/`)
  return data
}

export async function rerunTask(taskId: number): Promise<TaskSubmitResponse> {
  const { data } = await djangoClient.post<TaskSubmitResponse>(`/tasks/${taskId}/rerun/`)
  return data
}

export async function clearTasks(): Promise<TaskDeleteResponse & { data?: { deleted?: number } }> {
  const { data } = await djangoClient.post<TaskDeleteResponse & { data?: { deleted?: number } }>(
    "/tasks/clear/",
  )
  return data
}

export async function getTask(taskId: number): Promise<TaskDetailResponse> {
  const { data } = await djangoClient.get<TaskDetailResponse>(`/tasks/${taskId}/`)
  return data
}

export interface TaskMediaLink {
  url: string

  expires: number

  expires_at: string
}

export async function createTaskMediaLink(
  taskId: number,
  mediaId: number,
): Promise<{ status: boolean; message?: string; data?: TaskMediaLink }> {
  const { data } = await djangoClient.post<{
    status: boolean
    message?: string
    data?: TaskMediaLink
  }>(`/tasks/${taskId}/media/${mediaId}/link/`)
  return data
}

export async function getTaskMedia(taskId: number, mediaId: number): Promise<Blob> {
  const { data } = await djangoClient.get<Blob>(`/tasks/${taskId}/media/${mediaId}/`, {
    responseType: "blob",
  })
  return data
}
