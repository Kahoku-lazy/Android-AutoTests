export interface CaseIdentityRow {
  project?: string
  title?: string
}

export function caseHover(rows: CaseIdentityRow[] | undefined): string {
  const items = rows || []
  if (items.length < 2) return ""
  return items
    .map((row) => `${row.project || "未命名项目"} / ${row.title || "未命名用例"}`)
    .join("\n")
}
