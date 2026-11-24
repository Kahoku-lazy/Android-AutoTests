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

/** 全局检索配置：全库共用一份。 */
export interface RetrievalSettings {
  configured: boolean
  embedding_model_id: number | null
  top_k: number
  score_threshold: number
  chunk_size: number
  chunk_overlap: number
  index_epoch: number
  reindex_required: boolean
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

// ── 自动评测 ──

/** 评测指标（后端 eval_metrics.summarize 形状） */
export interface EvalMetrics {
  n_pos: number
  n_neg: number
  recall_at_1: number
  recall_at_3: number
  recall_at_5: number
  mrr: number
  false_hit_rate: number
}

/** 评测运行 */
export interface EvalRun {
  id: number
  run_id: string
  module_name: string
  model_snapshot: {
    provider: string
    api_key_env: string
    model_name: string
    base_url: string
  }
  pos_count: number
  neg_count: number
  status: "pending" | "running" | "done" | "failed"
  phase: string
  progress_done: number
  progress_total: number
  metrics: Partial<EvalMetrics>
  cost_estimate: {
    chat_input_tokens?: number
    chat_output_tokens?: number
    embedding_tokens?: number
    note?: string
  }
  error: string
  created_at: string
  updated_at: string
}

/** 评测逐题明细 */
export interface EvalQuery {
  id: number
  kind: "positive" | "negative"
  question: string
  gold_document_id: string
  gold_source: string
  source_chunk_index: number
  source_text: string
  hits: KnowledgeHit[]
  rank: number | null
  is_hit: boolean
}

/** 运行详情（含逐题） */
export interface EvalRunDetail extends EvalRun {
  queries: EvalQuery[]
}

/** 运营模型配置（只读引用，chat 类用于出题） */
export interface EvalModelConfig {
  id: number
  provider: string
  model_name: string
  model_kind?: string
  api_key_env: string
  base_url: string
}

/** 触发评测入参 */
export interface EvalTriggerPayload {
  module_id: number
  model_config_id: number
  pos_count?: number
  neg_count?: number
}
