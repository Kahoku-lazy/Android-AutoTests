/** 知识库检索 API — 模块登记 / 多选提问 / 预建索引 / 自动评测（后端 apps/knowledge_search）。 */
import djangoClient from "@/shared/api-client"
import type {
  EvalModelConfig,
  EvalRun,
  EvalRunDetail,
  EvalTriggerPayload,
  IndexOutcome,
  KnowledgeModuleRow,
  ModulePayload,
  QueryResult,
} from "./types"

export async function fetchKnowledgeModules(): Promise<{
  status: boolean
  data?: { modules?: KnowledgeModuleRow[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/knowledge-search/modules/")
  return data
}

/** 新增模块（仅超管）：一个模块 = 一个服务器本地资料目录。 */
export async function createKnowledgeModule(payload: ModulePayload): Promise<{
  status: boolean
  data?: KnowledgeModuleRow
  message?: string
}> {
  const { data } = await djangoClient.post("/knowledge-search/modules/", payload)
  return data
}

/** 编辑模块（仅超管）：含改路径与启停。 */
export async function updateKnowledgeModule(
  id: number,
  payload: Partial<ModulePayload>,
): Promise<{ status: boolean; data?: KnowledgeModuleRow; message?: string }> {
  const { data } = await djangoClient.patch(`/knowledge-search/modules/${id}/`, payload)
  return data
}

/** 删除模块登记（仅超管）：不碰资料目录与索引文件。 */
export async function deleteKnowledgeModule(id: number): Promise<{
  status: boolean
  data?: { deleted: boolean }
  message?: string
}> {
  const { data } = await djangoClient.delete(`/knowledge-search/modules/${id}/`)
  return data
}

/** 预建索引（仅超管）：同步增量重建，返回重建文件数。 */
export async function indexKnowledgeModule(id: number): Promise<{
  status: boolean
  data?: IndexOutcome
  message?: string
}> {
  const { data } = await djangoClient.post(`/knowledge-search/modules/${id}/index/`, {})
  return data
}

/** 勾选模块提问：返回检索原文与三态结果。 */
export async function queryKnowledge(payload: {
  question: string
  bases: string[]
}): Promise<{ status: boolean; data?: QueryResult; message?: string }> {
  const { data } = await djangoClient.post("/knowledge-search/query/", payload)
  return data
}

// ── 自动评测 ──

/** 评测运行列表（登录可读，可按模块过滤）。 */
export async function fetchEvalRuns(module?: string): Promise<{
  status: boolean
  data?: { runs?: EvalRun[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/knowledge-search/evaluations/", {
    params: module ? { module } : {},
  })
  return data
}

/** 评测运行详情：进度 / 指标 / 逐题明细。 */
export async function fetchEvalRun(id: number): Promise<{
  status: boolean
  data?: EvalRunDetail
  message?: string
}> {
  const { data } = await djangoClient.get(`/knowledge-search/evaluations/${id}/`)
  return data
}

/** 触发自动评测（仅超管）：后台执行，返回 pending 运行。 */
export async function triggerEval(payload: EvalTriggerPayload): Promise<{
  status: boolean
  data?: EvalRun
  message?: string
}> {
  const { data } = await djangoClient.post("/knowledge-search/evaluations/", payload)
  return data
}

/** 运营模型配置清单（只读引用）：出题模型下拉从这里来。 */
export async function fetchEvalModelConfigs(): Promise<{
  status: boolean
  data?: { configs?: EvalModelConfig[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/model-configs/", { params: { selectable: 1 } })
  return data
}
