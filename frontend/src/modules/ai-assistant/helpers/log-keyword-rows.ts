/** log-keyword-rows — 日志关键词对照表 → 表格行与搜索（纯函数，无 HTTP） */
import type { LogKeywordEntry } from "../api/toolbox"

/** 表格一行 = 一个「关键词 × 功能点」（一个关键词对应多个功能点就出现多行） */
export interface LogKeywordRow {
  /** 行标识（关键词 + 模块 + 编号 + 名称），供表格 row-key 使用 */
  key: string
  keyword: string
  module: string
  featureId?: number
  featureName: string
}

/** 模块 / 功能点缺名时的占位（后端数据缺失也要能读） */
export const UNNAMED_MODULE = "未标注模块"
export const UNNAMED_FEATURE = "未标注功能点"

/**
 * 对照表 → 表格行。
 *
 * 顺序口径：**保持表内顺序** —— 关键词按其在对照表中的先后，同一关键词的功能点按表内先后；
 * 前端不重排、不合并（排查时行序与数据文件一致才便于对照）。
 */
export function buildKeywordRows(entries: LogKeywordEntry[]): LogKeywordRow[] {
  const rows: LogKeywordRow[] = []
  for (const entry of entries) {
    const keyword = (entry.keyword || "").trim()
    if (!keyword) continue
    for (const feature of entry.features || []) {
      const module = (feature.module || "").trim() || UNNAMED_MODULE
      const featureName = (feature.feature || "").trim() || UNNAMED_FEATURE
      rows.push({
        key: `${keyword}|${module}|${feature.id ?? ""}|${featureName}`,
        keyword,
        module,
        featureId: feature.id,
        featureName,
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

/** 全量计数（关键词去重；功能点按「模块 + 编号 + 名称」去重）——搜索时也报全量，不缩水 */
export function keywordRowCounts(rows: LogKeywordRow[]): { keywords: number; features: number } {
  const keywords = new Set<string>()
  const features = new Set<string>()
  for (const row of rows) {
    keywords.add(row.keyword)
    features.add(`${row.module}|${row.featureId ?? ""}|${row.featureName}`)
  }
  return { keywords: keywords.size, features: features.size }
}
