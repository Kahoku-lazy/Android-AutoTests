import { BUSINESS_OPTIONS } from "../types"
import type { CaseRow, CaseStep, Priority, SheetView } from "../types"

export interface SheetGroupHeader {
  __group: string
  __count: number
}

export type SheetDisplayRow = CaseRow | SheetGroupHeader

export interface SheetGroup {
  name: string
  rows: CaseRow[]
}

export interface DraftIssue {
  message: string

  step: number
}

export function isGroupHeader(row: SheetDisplayRow): row is SheetGroupHeader {
  return typeof (row as SheetGroupHeader).__group === "string"
}

export function filterRows(rows: CaseRow[], filters: Record<string, string>): CaseRow[] {
  const active = Object.entries(filters).filter(([, value]) => value)
  if (!active.length) return [...rows]
  return rows.filter((row) =>
    active.every(([key, value]) => String(row[key as keyof CaseRow] ?? "").includes(value)),
  )
}

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

export function buildDisplayRows(groups: SheetGroup[]): SheetDisplayRow[] {
  const display: SheetDisplayRow[] = []
  for (const group of groups) {
    if (group.name) display.push({ __group: group.name, __count: group.rows.length })
    display.push(...group.rows)
  }
  return display
}

export function applySheetView(rows: CaseRow[], view: SheetView): SheetDisplayRow[] {
  const filtered = filterRows(rows, view.filters || {})
  const sorted = sortRows(filtered, view.sort)
  return buildDisplayRows(groupRows(sorted, view.group_by || ""))
}

export function cloneRow(row: CaseRow): CaseRow {
  return JSON.parse(JSON.stringify(row)) as CaseRow
}

export function hasAnchor(step: CaseStep): boolean {
  return Boolean(step.anchor && Object.keys(step.anchor).length)
}

export function hasLog(step: CaseStep): boolean {
  return Boolean(step.log && Object.keys(step.log).length)
}

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

export function priorityTone(priority: Priority): string {
  return priority.toLowerCase()
}

export function businessLabel(businessType: string): string {
  const hit = BUSINESS_OPTIONS.find((option) => option.value === businessType)
  return hit ? hit.label : businessType
}

export function stepSummary(count: number): string {
  return `${count || 0} 步`
}
