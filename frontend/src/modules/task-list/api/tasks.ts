/** Task publishing API — TypeScript */
import djangoClient from "@/shared/api-client"
import type {
  TaskDeleteResponse,
  TaskDetailResponse,
  TaskListResponse,
  TaskStatsResponse,
  TaskSubmitResponse,
} from "@/shared/types/ai"

/** 取一份平台报告的 HTML 正文。新窗口不能带登录头，所以先在这里取。 */
export async function fetchTaskReport(run: string, name: string): Promise<string> {
  const { data } = await djangoClient.get<{ status: boolean; data?: { content?: string } }>(
    `/ai/agent-reports/${encodeURIComponent(run)}/${encodeURIComponent(name)}/`,
  )
  return data.data?.content || ""
}

/** 任务列表 */
export async function listTasks(params?: {
  workflow_id?: number
  status?: string
}): Promise<TaskListResponse> {
  const { data } = await djangoClient.get<TaskListResponse>("/tasks/", { params })
  return data
}

/** 任务状态统计（总数 / 成功率 / 执行中 / 四类结果） */
export async function getTaskStats(): Promise<TaskStatsResponse> {
  const { data } = await djangoClient.get<TaskStatsResponse>("/tasks/stats/")
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

/** 任务截图短时直链 */
export interface TaskMediaLink {
  /** 相对路径，前端按当前 origin 补全 */
  url: string
  /** 过期时刻（Unix 秒） */
  expires: number
  /** 过期时刻（ISO 8601） */
  expires_at: string
}

/** 为可见截图签发短时直链（浏览器新标签可直接打开） */
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

/** 任务截图缩略图字节（WebP blob；报告只给 media_id） */
export async function getTaskMedia(taskId: number, mediaId: number): Promise<Blob> {
  const { data } = await djangoClient.get<Blob>(`/tasks/${taskId}/media/${mediaId}/`, {
    responseType: "blob",
  })
  return data
}
