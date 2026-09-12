/** Toolbox + MCP + Skills + Knowledge Base API — TypeScript */
import djangoClient from '@/shared/api-client'
import type {
  ToolboxListResponse,
  AgentOpResponse,
  KnowledgeStatusResponse,
} from '@/shared/types/ai'

// ── 共享工具箱项 / 知识库文档 DTO（类型跟着实现走，消费方从此处 import） ──
export interface SharedToolItem {
  id: number
  name: string
  item_type: string
  description?: string
  config_json?: string
  enabled: boolean
  created_at?: string
  origin?: 'local' | 'uploaded'
  missing?: boolean
}

export interface SkillTreeNode {
  name: string
  path: string
  is_dir: boolean
  children?: SkillTreeNode[]
}

export interface SkillFilePayload {
  path: string
  name: string
  kind: 'markdown' | 'text' | 'unsupported' | 'too_large'
  content: string
}

export interface KnowledgeDoc {
  id: number | string
  name?: string
  source?: string
  type?: string
  size?: number
  ext?: string
}

export interface KnowledgePreviewPayload {
  path: string
  name: string
  kind: 'markdown' | 'text'
  content: string
  converted?: boolean
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

export async function toggleSharedTool(itemId: number, enabled: boolean): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/toggle`, { enabled })
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

export async function fetchSharedSkillTree(
  name: string,
): Promise<{ status: boolean; data?: { name?: string; tree?: SkillTreeNode[] }; message?: string }> {
  const { data } = await djangoClient.get(`/ai/toolbox/skills/${encodeURIComponent(name)}/tree`)
  return data
}

export async function fetchSharedSkillFile(
  name: string,
  path: string,
): Promise<{ status: boolean; data?: SkillFilePayload; message?: string }> {
  const { data } = await djangoClient.get(`/ai/toolbox/skills/${encodeURIComponent(name)}/file`, {
    params: { path },
  })
  return data
}

// ── 平台配置（平台唯一智能体的工具/知识库配置，AI 工具箱 / 知识库页读写） ──

export interface PlatformConfig {
  agent_id?: number
  agent_name?: string
  enable_workspace_tools: boolean
  enable_business_tools: boolean
  enable_mcp_tools: boolean
  enable_skills: boolean
  enable_knowledge_base: boolean
  skills_config: Record<string, boolean>
  knowledge_sources: Record<string, boolean>
}

export async function fetchPlatformConfig(): Promise<{ status: boolean; data?: PlatformConfig; message?: string }> {
  const { data } = await djangoClient.get('/ai/platform-config')
  return data
}

export async function updatePlatformConfig(payload: Partial<PlatformConfig>): Promise<{ status: boolean; data?: PlatformConfig; message?: string }> {
  const { data } = await djangoClient.post('/ai/platform-config/update', payload)
  return data
}

// ── Platform tools ──

export interface PlatformToolItem {
  name: string
  summary: string
  icon: string
  read_only: boolean
  enabled: boolean
}

export interface PlatformToolCategory {
  key: string
  icon: string
  color: string
  tools: PlatformToolItem[]
}

export async function fetchPlatformTools(): Promise<{ status: boolean; data?: { categories?: PlatformToolCategory[] }; message?: string }> {
  const { data } = await djangoClient.get('/ai/available-tools')
  return data
}

export async function togglePlatformTool(payload: {
  name?: string
  category?: string
  enabled: boolean
}): Promise<{ status: boolean; data?: { updated?: string[] }; message?: string }> {
  const { data } = await djangoClient.post('/ai/platform-tools/toggle', payload)
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

export async function addKnowledgeDocument(
  file: File,
  subdir = '',
): Promise<{ status: boolean; data?: KnowledgeDoc; message?: string }> {
  const formData = new FormData()
  formData.append('file', file)
  if (subdir) formData.append('subdir', subdir)
  const { data } = await djangoClient.post('/ai/knowledge/documents/add', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function previewKnowledgeDocument(
  path: string,
): Promise<{ status: boolean; data?: KnowledgePreviewPayload; message?: string }> {
  const { data } = await djangoClient.get('/ai/knowledge/documents/preview', { params: { path } })
  return data
}
