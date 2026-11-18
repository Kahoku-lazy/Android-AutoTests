/** log-keyword-rows — 日志关键词对照表 → 表格行与搜索 / 范围筛选（纯函数，无 HTTP） */
import type { LogKeywordEntry, LogKeywordFeature } from "../api"

/** 通用范围值（与引擎层 DEFAULT_CHANNEL="*" 及后端 sl_log_keywords.scope 约定对齐） */
export const SCOPE_GENERAL = "*"

/** 范围筛选的「全部」选项值 */
export const SCOPE_FILTER_ALL = "all"

/**
 * 带范围的功能点条目。
 *
 * 后端契约（api.ts 的 LogKeywordFeature）补 scope 字段前，经此交叉类型读取；
 * 补齐后结构天然兼容，届时可收敛回 LogKeywordFeature。
 */
export type LogKeywordScopedFeature = LogKeywordFeature & { scope?: string }

/** 表格一行 = 一个「关键词 × 功能点 × 范围」（一个关键词对应多个功能点就出现多行） */
export interface LogKeywordRow {
  /** 行标识（关键词 + 模块 + 编号 + 名称 + 范围），供表格 row-key 使用 */
  key: string
  /** 条目主键（编辑 / 删除定位用；旧响应缺省时为空） */
  rowId?: number
  keyword: string
  module: string
  featureId?: number
  featureName: string
  /** 范围："*"=通用；否则 SKU 名（如 H6601） */
  scope: string
}

/** 模块 / 功能点缺名时的占位（后端数据缺失也要能读） */
export const UNNAMED_MODULE = "未标注模块"
export const UNNAMED_FEATURE = "未标注功能点"

/** 范围展示口径：通用 / <SKU>专用（如「H6601专用」） */
export function scopeLabel(scope: string): string {
  return scope === SCOPE_GENERAL ? "通用" : `${scope}专用`
}

/**
 * 对照表 → 表格行。
 *
 * 顺序口径：**保持表内顺序** —— 关键词按其在对照表中的先后，同一关键词的功能点按表内先后；
 * 前端不重排、不合并（排查时行序与数据表一致才便于对照）。
 * 范围缺省按通用处理（兼容尚未带 scope 的旧响应）。
 */
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

/** 忽略大小写的包含匹配：关键词 / 模块名 / 功能点名任一命中即保留该行 */
export function filterKeywordRows(rows: LogKeywordRow[], query: string): LogKeywordRow[] {
  const q = (query || "").trim().toLowerCase()
  if (!q) return rows
  const hit = (text: string): boolean => text.toLowerCase().includes(q)
  return rows.filter((row) => hit(row.keyword) || hit(row.module) || hit(row.featureName))
}

/** 范围筛选：空值或「全部」返回全量；否则按范围精确匹配（与搜索可叠加） */
export function filterKeywordRowsByScope(rows: LogKeywordRow[], scope: string): LogKeywordRow[] {
  if (!scope || scope === SCOPE_FILTER_ALL) return rows
  return rows.filter((row) => row.scope === scope)
}

/** 范围下拉选项：按全量行首次出现顺序派生，通用恒在首位（存在时），其余 SKU 依出现先后 */
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

/** 全量计数（关键词去重；功能点按「模块 + 编号 + 名称」去重）——搜索 / 范围筛选时也报全量，不缩水；范围不参与去重 */
export function keywordRowCounts(rows: LogKeywordRow[]): { keywords: number; features: number } {
  const keywords = new Set<string>()
  const features = new Set<string>()
  for (const row of rows) {
    keywords.add(row.keyword)
    features.add(`${row.module}|${row.featureId ?? ""}|${row.featureName}`)
  }
  return { keywords: keywords.size, features: features.size }
}
