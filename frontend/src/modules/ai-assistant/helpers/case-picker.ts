export interface CaseRow {
  id: string
  title: string
}

export interface CaseProjectGroup {
  id: number
  name: string
  rows: CaseRow[]
}

export interface PickedSummary {
  count: number

  projectCount: number

  names: string[]

  rest: number
}

const SUMMARY_NAME_LIMIT = 4

export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase()
}

export function matchesCase(row: CaseRow, query: string): boolean {
  if (!query) return true
  return row.title.toLowerCase().includes(query) || row.id.toLowerCase().includes(query)
}

export function filterCaseProjects(
  projects: CaseProjectGroup[],
  query: string,
): CaseProjectGroup[] {
  const keyword = normalizeQuery(query)
  return projects
    .map((project) => ({
      ...project,
      rows: project.rows.filter((row) => matchesCase(row, keyword)),
    }))
    .filter((project) => project.rows.length > 0)
}

export function countHitCases(groups: CaseProjectGroup[]): number {
  return groups.reduce((total, group) => total + group.rows.length, 0)
}

export function pickableIds(groups: CaseProjectGroup[]): string[] {
  return groups.flatMap((group) => group.rows.map((row) => row.id))
}

export function toggleAll(selected: string[], ids: string[]): string[] {
  if (!ids.length) return [...selected]
  const allPicked = ids.every((id) => selected.includes(id))
  if (allPicked) return selected.filter((id) => !ids.includes(id))
  const added = ids.filter((id) => !selected.includes(id))
  return [...selected, ...added]
}

export function hitbarText(input: {
  inScope: number
  elsewhere: number
  projectName: string
}): string {
  if (input.elsewhere <= 0) return ""
  if (input.inScope > 0) {
    return `当前项目命中 ${input.inScope} 条，另有 ${input.elsewhere} 条在其他项目命中`
  }
  return `「${input.projectName}」没有命中，另有 ${input.elsewhere} 条在其他项目命中`
}

export function summarizePicked(selected: string[], projects: CaseProjectGroup[]): PickedSummary {
  const rows = selected
    .map((id) => findCase(projects, id))
    .filter((row): row is { row: CaseRow; project: CaseProjectGroup } => row !== null)
  const projectNames = new Set(rows.map((item) => item.project.name))
  return {
    count: selected.length,
    projectCount: projectNames.size,
    names: rows.slice(0, SUMMARY_NAME_LIMIT).map((item) => item.row.title),
    rest: Math.max(rows.length - SUMMARY_NAME_LIMIT, 0),
  }
}

export function findCase(
  projects: CaseProjectGroup[],
  caseId: string,
): { row: CaseRow; project: CaseProjectGroup } | null {
  for (const project of projects) {
    const row = project.rows.find((item) => item.id === caseId)
    if (row) return { row, project }
  }
  return null
}
