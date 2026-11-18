/** 知识库检索页 DTO：与后端 apps/knowledge_search 契约对齐（snake_case）。 */

/** 模块登记行 */
export interface KnowledgeModuleRow {
  id: number
  name: string
  description: string
  data_dir: string
  enabled: boolean
  created_at: string
  updated_at: string
}

/** 一条未经改写的检索命中 */
export interface KnowledgeHit {
  base: string
  source: string
  text: string
  score: number
  chunk_index: number
  document_id: string
}

export type QueryResultStatus = "ok" | "no_hit" | "unavailable"

/** 提问结果：三态 + 命中 + 逐库错误 */
export interface QueryResult {
  result: QueryResultStatus
  hits: KnowledgeHit[]
  errors: string[]
}

/** 新增/编辑模块入参 */
export interface ModulePayload {
  name: string
  description: string
  data_dir: string
  enabled?: boolean
}

/** 预建索引结果 */
export interface IndexOutcome {
  ok: boolean
  error: string
  reindexed: number
}
