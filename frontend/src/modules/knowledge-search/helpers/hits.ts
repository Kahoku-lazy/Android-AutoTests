/** 检索命中纯函数：排序、展示格式化与稳定键。无状态无副作用。 */
import type { KnowledgeHit } from "../types"

/** 按相似度降序排（后端已排序，这里做展示层防御性排序，不改原文）。 */
export function sortHits(hits: KnowledgeHit[]): KnowledgeHit[] {
  return [...hits].sort((left, right) => right.score - left.score)
}

/** 相似度展示为百分比，保留一位小数。 */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

/** 命中的稳定键：文档编号 + 片段序号。 */
export function hitKey(hit: KnowledgeHit): string {
  return `${hit.document_id}:${hit.chunk_index}`
}
