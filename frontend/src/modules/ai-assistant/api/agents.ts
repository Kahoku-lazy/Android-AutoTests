/** Agent CRUD API — TypeScript */
import djangoClient from "@/shared/api-client"
import type { AgentListResponse, AgentDetailResponse, AgentOpResponse } from "@/shared/types/ai"

/** 获取所有 Agent 列表 */
export async function listAgents(): Promise<AgentListResponse> {
  const { data } = await djangoClient.get<AgentListResponse>("/ai/agents/")
  return data
}

/** 获取 Agent 详情 */
export async function getAgentDetail(agentId: number): Promise<AgentDetailResponse> {
  const { data } = await djangoClient.get<AgentDetailResponse>(`/ai/agents/${agentId}/`)
  return data
}

/** 上传头像 */
export async function uploadAvatar(formData: FormData): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>("/ai/upload-avatar/", formData)
  return data
}

/** 上传文件 / 图片（multipart；勿带默认 application/json） */
export async function uploadFile(formData: FormData): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>("/ai/upload-file/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

/** 保存 Agent（新建或更新） */
export async function saveAgent(
  isNew: boolean,
  agentId: number | null,
  payload: object,
): Promise<AgentDetailResponse> {
  const url = isNew ? "/ai/agents/create/" : `/ai/agents/${agentId}/update/`
  const { data } = await djangoClient.post<AgentDetailResponse>(url, payload)
  return data
}
