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
  RetrievalSettings,
} from "./types"

export async function fetchKnowledgeModules(): Promise<{
  status: boolean
  data?: { modules?: KnowledgeModuleRow[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/knowledge-search/modules/")
  return data
}

export async function createKnowledgeModule(payload: ModulePayload): Promise<{
  status: boolean
  data?: KnowledgeModuleRow
  message?: string
}> {
  const { data } = await djangoClient.post("/knowledge-search/modules/", payload)
  return data
}

export async function updateKnowledgeModule(
  id: number,
  payload: Partial<ModulePayload>,
): Promise<{ status: boolean; data?: KnowledgeModuleRow; message?: string }> {
  const { data } = await djangoClient.patch(`/knowledge-search/modules/${id}/`, payload)
  return data
}

export async function deleteKnowledgeModule(id: number): Promise<{
  status: boolean
  data?: { deleted: boolean }
  message?: string
}> {
  const { data } = await djangoClient.delete(`/knowledge-search/modules/${id}/`)
  return data
}

export async function indexKnowledgeModule(id: number): Promise<{
  status: boolean
  data?: IndexOutcome
  message?: string
}> {
  const { data } = await djangoClient.post(`/knowledge-search/modules/${id}/index/`, {})
  return data
}

export async function fetchRetrievalSettings(): Promise<{
  status: boolean
  data?: RetrievalSettings
  message?: string
}> {
  const { data } = await djangoClient.get("/knowledge-search/settings/")
  return data
}

export async function saveRetrievalSettings(
  payload: Omit<RetrievalSettings, "configured" | "index_epoch" | "reindex_required">,
): Promise<{ status: boolean; data?: RetrievalSettings; message?: string }> {
  const { data } = await djangoClient.put("/knowledge-search/settings/", payload)
  return data
}

export async function queryKnowledge(payload: {
  question: string
  bases: string[]
}): Promise<{ status: boolean; data?: QueryResult; message?: string }> {
  const { data } = await djangoClient.post("/knowledge-search/query/", payload)
  return data
}

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

export async function fetchEvalRun(id: number): Promise<{
  status: boolean
  data?: EvalRunDetail
  message?: string
}> {
  const { data } = await djangoClient.get(`/knowledge-search/evaluations/${id}/`)
  return data
}

export async function triggerEval(payload: EvalTriggerPayload): Promise<{
  status: boolean
  data?: EvalRun
  message?: string
}> {
  const { data } = await djangoClient.post("/knowledge-search/evaluations/", payload)
  return data
}

export async function fetchEvalModelConfigs(modelKind = ""): Promise<{
  status: boolean
  data?: { configs?: EvalModelConfig[] }
  message?: string
}> {
  const params: Record<string, string> = modelKind ? { model_kind: modelKind } : { selectable: "1" }
  const { data } = await djangoClient.get("/ai/model-configs/", { params })
  return data
}
