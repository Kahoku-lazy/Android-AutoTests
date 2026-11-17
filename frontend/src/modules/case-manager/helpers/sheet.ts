/**
 * python -m 调试路径: 不适用（前端 Vue 模块，纯函数见 frontend/tests/case-manager）
 *
 * 本模块的业务功能如下：
 * 1. 视图计算: applySheetView 把行按个人视图做筛选 / 排序 / 分组。
 * 2. 组头哨兵: buildDisplayRows 在分组之间插入组头行，供单张表合并行渲染。
 * 3. 草稿读写: cloneRow / editablePayload / validateDraft 支撑抽屉编辑与逐行保存。
 * 4. 展示文案: priorityTone / businessLabel / stepSummary 把枚举翻成标签与文案。
 */
import { BUSINESS_OPTIONS } from "../types"
import type { CaseRow, CaseStep, Priority, SheetView } from "../types"

/** 组头行：只在渲染期存在，不是 CaseRow */
export interface SheetGroupHeader {
  __group: string
  __count: number
}

/** 组头或真实用例行 */
export type SheetDisplayRow = CaseRow | SheetGroupHeader

/** 一组行（组名 + 行） */
export interface SheetGroup {
  name: string
  rows: CaseRow[]
}

/** 抽屉校验失败的位置与原因 */
export interface DraftIssue {
  message: string
  /** 出错的步骤序号（从 1 开始）；非步骤问题为 0 */
  step: number
}

/**
 * 判定一行是不是组头哨兵。
 *
 * Args:
 *   row: 表格数据里的一行。
 *
 * Returns:
 *   是组头返回 true。
 */
export function isGroupHeader(row: SheetDisplayRow): row is SheetGroupHeader {
  return typeof (row as SheetGroupHeader).__group === "string"
}

/**
 * 按个人视图筛选：每个字段做包含匹配，空值视为不筛。
 *
 * Args:
 *   rows: 原始行。
 *   filters: 视图里的字段 → 关键字。
 *
 * Returns:
 *   过滤后的行（保持入参顺序）。
 */
export function filterRows(rows: CaseRow[], filters: Record<string, string>): CaseRow[] {
  const active = Object.entries(filters).filter(([, value]) => value)
  if (!active.length) return [...rows]
  return rows.filter((row) =>
    active.every(([key, value]) => String(row[key as keyof CaseRow] ?? "").includes(value)),
  )
}

/**
 * 按视图排序：数值字段按数值比，其余按字符串比。
 *
 * Args:
 *   rows: 待排序行。
 *   sort: 视图里的排序设置。
 *
 * Returns:
 *   新数组，不改入参。
 */
export function sortRows(rows: CaseRow[], sort: SheetView["sort"]): CaseRow[] {
  const field = (sort?.field || "sort_order") as keyof CaseRow
  const direction = sort?.direction === "desc" ? -1 : 1
  return [...rows].sort((left, right) => {
    const a = left[field]
    const b = right[field]
    if (typeof a === "number" && typeof b === "number") return (a - b) * direction
    return String(a ?? "").localeCompare(String(b ?? "")) * direction
  })
}

/**
 * 按字段折成组；未分组时返回单个空名组。
 *
 * Args:
 *   rows: 已筛选排序的行。
 *   groupBy: 字段名；空串表示不分组。
 *
 * Returns:
 *   组列表。
 */
export function groupRows(rows: CaseRow[], groupBy: string): SheetGroup[] {
  if (!groupBy) return [{ name: "", rows }]
  const buckets = new Map<string, CaseRow[]>()
  for (const row of rows) {
    const name = String(row[groupBy as keyof CaseRow] ?? "") || "未分组"
    const bucket = buckets.get(name)
    if (bucket) bucket.push(row)
    else buckets.set(name, [row])
  }
  return [...buckets.entries()].map(([name, groupRowsOfName]) => ({
    name,
    rows: groupRowsOfName,
  }))
}

/**
 * 把组摊平成「组头哨兵 + 行」的一维数组，供单张表用 span-method 合并。
 *
 * Args:
 *   groups: groupRows 的产物。
 *
 * Returns:
 *   含组头行的展示数据；不分组时原样返回行。
 */
export function buildDisplayRows(groups: SheetGroup[]): SheetDisplayRow[] {
  const display: SheetDisplayRow[] = []
  for (const group of groups) {
    if (group.name) display.push({ __group: group.name, __count: group.rows.length })
    display.push(...group.rows)
  }
  return display
}

/**
 * 视图入口：筛选 → 排序 → 分组 → 摊平。
 *
 * Args:
 *   rows: 服务端行。
 *   view: 个人视图。
 *
 * Returns:
 *   可直接交给表纸的展示数据。
 */
export function applySheetView(rows: CaseRow[], view: SheetView): SheetDisplayRow[] {
  const filtered = filterRows(rows, view.filters || {})
  const sorted = sortRows(filtered, view.sort)
  return buildDisplayRows(groupRows(sorted, view.group_by || ""))
}

/**
 * 深拷贝一行，作为抽屉草稿。
 *
 * 两个坑都踩过，注释留证：
 * 1. 不能按字段重建（如 `{...step.log, keywords: [...step.log.keywords]}`）——
 *    服务端给的空执行提示是 `{}` 而不是缺键，重建会假设 `log.keywords` 存在并直接抛 TypeError。
 * 2. 不能用 structuredClone —— 表格里的行是 Vue 的响应式 Proxy，Proxy 不可克隆，
 *    会抛 DataCloneError。
 * 因此走 JSON 快照：与形状无关，并且天然把草稿变成不带 Proxy 的普通对象。
 *
 * Args:
 *   row: 服务端行（可能来自 reactive 状态）。
 *
 * Returns:
 *   与入参无引用共享的新对象。
 */
export function cloneRow(row: CaseRow): CaseRow {
  return JSON.parse(JSON.stringify(row)) as CaseRow
}

/**
 * 这一步是否真的带页面锚点（`{}` 视为没有）。
 *
 * Args:
 *   step: 步骤。
 *
 * Returns:
 *   有任一锚点字段返回 true。
 */
export function hasAnchor(step: CaseStep): boolean {
  return Boolean(step.anchor && Object.keys(step.anchor).length)
}

/**
 * 这一步是否真的带日志证据（`{}` 视为没有）。
 *
 * Args:
 *   step: 步骤。
 *
 * Returns:
 *   有任一日志字段返回 true。
 */
export function hasLog(step: CaseStep): boolean {
  return Boolean(step.log && Object.keys(step.log).length)
}

/**
 * 只挑服务端可写的字段，避免把 step_count / updated_at 之类回传。
 *
 * 空执行提示不发送：功能项目的接口对「出现 anchor / log 键的步骤」直接拒收，
 * 而空提示发不发都不改变服务端结果。
 *
 * Args:
 *   row: 草稿行。
 *
 * Returns:
 *   逐行 PATCH 的请求体。
 */
export function editablePayload(row: CaseRow): Partial<CaseRow> {
  return {
    title: row.title.trim(),
    priority: row.priority,
    system: row.system,
    business_type: row.business_type,
    module: row.module,
    precondition: row.precondition,
    steps: (row.steps || []).map((step) => {
      const payload: CaseStep = {
        action: step.action.trim(),
        assertion: step.assertion.trim(),
      }
      if (hasAnchor(step)) payload.anchor = step.anchor
      if (hasLog(step)) payload.log = step.log
      return payload
    }),
  }
}

/**
 * 应用改动前的本地校验：与服务端同口径，但把错误定位到步骤序号。
 *
 * Args:
 *   row: 草稿行。
 *
 * Returns:
 *   有问题返回 DraftIssue，没问题返回 null。
 */
export function validateDraft(row: CaseRow): DraftIssue | null {
  if (!row.title.trim()) return { message: "标题不能为空", step: 0 }
  const steps = row.steps || []
  if (!steps.length) return { message: "至少要保留 1 条步骤", step: 0 }
  for (const [index, step] of steps.entries()) {
    if (!step.action.trim()) return { message: `第 ${index + 1} 步的动作不能为空`, step: index + 1 }
    if (!step.assertion.trim())
      return { message: `第 ${index + 1} 步的断言不能为空`, step: index + 1 }
    if (step.action.length > 2000)
      return { message: `第 ${index + 1} 步的动作超过 2000 字上限`, step: index + 1 }
    if (step.assertion.length > 2000)
      return { message: `第 ${index + 1} 步的断言超过 2000 字上限`, step: index + 1 }
  }
  return null
}

/**
 * 优先级 → chip 色调。
 *
 * Args:
 *   priority: P0 / P1 / P2。
 *
 * Returns:
 *   p0 / p1 / p2 之一。
 */
export function priorityTone(priority: Priority): string {
  return priority.toLowerCase()
}

/**
 * 业务类型枚举 → 中文文案。
 *
 * Args:
 *   businessType: 业务枚举值。
 *
 * Returns:
 *   中文标签；未知值原样返回。
 */
export function businessLabel(businessType: string): string {
  const hit = BUSINESS_OPTIONS.find((option) => option.value === businessType)
  return hit ? hit.label : businessType
}

/**
 * 步骤数 → 摘要文案。
 *
 * Args:
 *   count: 步骤条数。
 *
 * Returns:
 *   如「5 步」。
 */
export function stepSummary(count: number): string {
  return `${count || 0} 步`
}
