import type { LogKeywordEntry, LogKeywordFeature } from "../api"

export const SCOPE_GENERAL = "*"

export const SCOPE_FILTER_ALL = "all"

export type LogKeywordScopedFeature = LogKeywordFeature & { scope?: string }

export interface LogKeywordRow {
  key: string

  rowId?: number
  keyword: string
  module: string
  featureId?: number
  featureName: string

  scope: string
}

export const UNNAMED_MODULE = "未标注模块"
export const UNNAMED_FEATURE = "未标注功能点"

export function scopeLabel(scope: string): string {
  return scope === SCOPE_GENERAL ? "通用" : `${scope}专用`
}

export function buildKeywordRows(entries: LogKeywordEntry[]): LogKeywordRow[] {
  const rows: LogKeywordRow[] = []
  for (const entry of entries) {
    const keyword = (entry.keyword || "").trim()
    if (!keyword) continue
    for (const feature of (entry.features || []) as LogKeywordScopedFeature[]) {
      const module = (feature.module || "").trim() || UNNAMED_MODULE
      const featureName = (feature.feature || "").trim() || UNNAMED_FEATURE
      const scope = (feature.scope || "").trim() || SCOPE_GENERAL
      rows.push({
        key: `${keyword}|${module}|${feature.id ?? ""}|${featureName}|${scope}`,
        rowId: feature.row_id,
        keyword,
        module,
        featureId: feature.id,
        featureName,
        scope,
      })
    }
  }
  return rows
}

export function filterKeywordRows(rows: LogKeywordRow[], query: string): LogKeywordRow[] {
  const q = (query || "").trim().toLowerCase()
  if (!q) return rows
  const hit = (text: string): boolean => text.toLowerCase().includes(q)
  return rows.filter((row) => hit(row.keyword) || hit(row.module) || hit(row.featureName))
}

export function filterKeywordRowsByScope(rows: LogKeywordRow[], scope: string): LogKeywordRow[] {
  if (!scope || scope === SCOPE_FILTER_ALL) return rows
  return rows.filter((row) => row.scope === scope)
}

export function scopeOptions(rows: LogKeywordRow[]): { value: string; label: string }[] {
  const seen: string[] = []
  for (const row of rows) {
    if (!seen.includes(row.scope)) seen.push(row.scope)
  }
  const ordered = seen.includes(SCOPE_GENERAL)
    ? [SCOPE_GENERAL, ...seen.filter((scope) => scope !== SCOPE_GENERAL)]
    : seen
  return ordered.map((value) => ({ value, label: scopeLabel(value) }))
}

export function keywordRowCounts(rows: LogKeywordRow[]): { keywords: number; features: number } {
  const keywords = new Set<string>()
  const features = new Set<string>()
  for (const row of rows) {
    keywords.add(row.keyword)
    features.add(`${row.module}|${row.featureId ?? ""}|${row.featureName}`)
  }
  return { keywords: keywords.size, features: features.size }
}
