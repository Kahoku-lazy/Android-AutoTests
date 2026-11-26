import type { KnowledgeHit } from "../types"

export function sortHits(hits: KnowledgeHit[]): KnowledgeHit[] {
  return [...hits].sort((left, right) => right.score - left.score)
}

export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

export function hitKey(hit: KnowledgeHit): string {
  return `${hit.document_id}:${hit.chunk_index}`
}
