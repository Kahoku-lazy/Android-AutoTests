/** Agent CRUD API — TypeScript */
import djangoClient from '@/shared/api-client'
import type {
  AgentListResponse,
  AgentDetailResponse,
  AgentOpResponse,
  AgentTestResponse,
  AgentHealthResponse,
} from '@/shared/types/ai'

/** 获取所有 Agent 列表 */
export async function listAgents(): Promise<AgentListResponse> {
  const { data } = await djangoClient.get<AgentListResponse>('/ai/agents')
  return data
}

/** 获取 Agent 健康状态 */
export async function checkAgentsHealth(): Promise<AgentHealthResponse> {
  const { data } = await djangoClient.get<AgentHealthResponse>('/ai/agents/health')
  return data
}

/** 测试 Agent 连接 */
export async function testAgent(agentId: number): Promise<AgentTestResponse> {
  const { data } = await djangoClient.post<AgentTestResponse>(`/ai/agents/${agentId}/test`)
  return data
}

/** 删除 Agent */
export async function deleteAgent(agentId: number): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/agents/${agentId}/delete`)
  return data
}

/** 更新 Agent 模型名称 */
export async function updateAgentModel(agentId: number, modelName: string): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/agents/${agentId}/update`, { model_name: modelName })
  return data
}

/** 获取 Agent 详情 */
export async function getAgentDetail(agentId: number): Promise<AgentDetailResponse> {
  const { data } = await djangoClient.get<AgentDetailResponse>(`/ai/agents/${agentId}`)
  return data
}

/** 检测可用模型 */
export async function detectModels(payload: object): Promise<{ status: boolean; models?: string[]; message?: string }> {
  const { data } = await djangoClient.post('/ai/models/detect', payload)
  return data
}

/** 上传头像 */
export async function uploadAvatar(formData: FormData): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>('/ai/upload-avatar', formData)
  return data
}

/** 上传文件 / 图片（multipart；勿带默认 application/json） */
export async function uploadFile(formData: FormData): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>('/ai/upload-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** 保存 Agent（新建或更新） */
export async function saveAgent(isNew: boolean, agentId: number | null, payload: object): Promise<AgentDetailResponse> {
  const url = isNew ? "/ai/agents/create" : `/ai/agents/${agentId}/update`
  const { data } = await djangoClient.post<AgentDetailResponse>(url, payload)
  return data
}

