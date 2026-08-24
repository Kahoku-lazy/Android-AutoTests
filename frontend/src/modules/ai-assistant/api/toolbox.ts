/** Toolbox + MCP + Skills + Knowledge Base API — TypeScript */
import djangoClient from '@/shared/api-client'
import type {
  ToolboxListResponse,
  AgentOpResponse,
  KnowledgeStatusResponse,
} from '@/shared/types/ai'

// ── Agent 已导入工具副本 / 知识库文档 DTO（类型跟着实现走，消费方从此处 import） ──
export interface ToolItem {
  id?: number
  name: string
  tool_type?: string
  enabled?: boolean
  config_json?: string
  config?: object
}

export interface KnowledgeDoc {
  id: number | string
  name?: string
}

// ── Toolbox (shared tools / skills / extensions) ──

export async function fetchSharedTools(): Promise<ToolboxListResponse> {
  const { data } = await djangoClient.get<ToolboxListResponse>('/ai/toolbox')
  return data
}

export async function createSharedTool(payload: {
  name: string; item_type: string; description?: string; config_json?: object | string
}): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>('/ai/toolbox/create', {
    name: payload.name,
    item_type: payload.item_type,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

export async function updateSharedTool(itemId: number, payload: {
  name?: string; item_type?: string; description?: string; config_json?: object | string
}): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/update`, {
    name: payload.name,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

export async function deleteSharedTool(itemId: number): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/delete`)
  return data
}

export async function importFromToolbox(agentId: number, toolboxItemId: number): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(
    `/ai/agents/${agentId}/tools/import-from-toolbox`,
    { toolbox_item_id: toolboxItemId },
  )
  return data
}

export async function uploadSharedSkill(files: File[], name: string): Promise<AgentOpResponse> {
  const formData = new FormData()
  formData.append('name', name)
  for (const file of files) {
    formData.append('files', file, (file as unknown as { webkitRelativePath?: string }).webkitRelativePath || file.name)
  }
  const { data } = await djangoClient.post<AgentOpResponse>('/ai/toolbox/upload-skill', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ── Agent 已导入工具副本（来自工具箱） ──

export async function fetchAgentTools(agentId: number): Promise<{ status: boolean; data?: { mcp?: ToolItem[]; skills?: ToolItem[] }; message?: string }> {
  const { data } = await djangoClient.get(`/ai/agents/${agentId}/tools`)
  return data
}

export async function deleteToolById(agentId: number, toolId: number): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/agents/${agentId}/tools/${toolId}/delete`)
  return data
}

// ── Platform tools ──

export async function fetchPlatformTools(): Promise<{ status: boolean; data?: { categories?: object[] }; message?: string }> {
  const { data } = await djangoClient.get('/ai/available-tools')
  return data
}

export async function fetchAvailableSkills(): Promise<{ status: boolean; data?: { skills?: object[] }; message?: string }> {
  const { data } = await djangoClient.get('/ai/available-skills')
  return data
}

// ── Knowledge Base ──

export async function getKnowledgeStatus(): Promise<KnowledgeStatusResponse> {
  const { data } = await djangoClient.get<KnowledgeStatusResponse>('/ai/knowledge/status')
  return data
}

export async function getKnowledgeDocuments(): Promise<{ status: boolean; data?: { documents?: KnowledgeDoc[]; total?: number }; message?: string }> {
  const { data } = await djangoClient.get('/ai/knowledge/documents')
  return data
}

export async function reindexKnowledge(): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>('/ai/knowledge/reindex')
  return data
}
