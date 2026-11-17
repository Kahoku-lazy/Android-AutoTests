/**
 * 平台用例选择器的纯函数：过滤、分组、计数与已选摘要。
 *
 * 这一层不碰 DOM 也不发请求：组件只把数据传进来，拿返回的分组去渲染，
 * 因此「按编号搜」「切项目不清空」这类口径可以直接用单测锁住。
 */

/** 自动化用例的一行：接口只给编号与标题。 */
export interface CaseRow {
  id: string
  title: string
}

/** 一个自动化项目及其用例，与 `GET /cases/projects/automation/` 的 data 项一一对应。 */
export interface CaseProjectGroup {
  id: number
  name: string
  rows: CaseRow[]
}

/** 左栏「已选用例」摘要卡要显示的东西。 */
export interface PickedSummary {
  /** 已选条数 */
  count: number
  /** 覆盖的项目数 */
  projectCount: number
  /** 摘要里列出的用例名（最多 4 条） */
  names: string[]
  /** 未列出的剩余条数 */
  rest: number
}

/** 摘要卡最多列几条用例名，超出部分折成「还有 N 条」。 */
const SUMMARY_NAME_LIMIT = 4

/**
 * 归一化搜索词：去首尾空白并转小写。
 *
 * @param query 用户输入。
 * @returns 用于比较的搜索词；空串表示不筛选。
 */
export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase()
}

/**
 * 判断一条用例是否命中搜索词（标题或编号任一包含即可）。
 *
 * @param row 用例行。
 * @param query 已归一化的搜索词。
 * @returns 命中为 true。
 */
export function matchesCase(row: CaseRow, query: string): boolean {
  if (!query) return true
  return row.title.toLowerCase().includes(query) || row.id.toLowerCase().includes(query)
}

/**
 * 按搜索词过滤项目，只保留仍有命中的项目与命中行。
 *
 * @param projects 全部自动化项目。
 * @param query 用户输入（函数内部归一化）。
 * @returns 过滤后的分组；无命中时为空数组。
 */
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

/**
 * 统计分组内的用例总数（已过滤的分组得到命中数）。
 *
 * @param groups 分组列表。
 * @returns 条数。
 */
export function countHitCases(groups: CaseProjectGroup[]): number {
  return groups.reduce((total, group) => total + group.rows.length, 0)
}

/**
 * 收集可勾选的用例编号，保持列表顺序。
 *
 * @param groups 分组列表。
 * @returns 用例编号数组。
 */
export function pickableIds(groups: CaseProjectGroup[]): string[] {
  return groups.flatMap((group) => group.rows.map((row) => row.id))
}

/**
 * 全选 / 全不选：给定的编号已全部选中时整体移除，否则整体加入。
 *
 * @param selected 当前已选编号。
 * @param ids 本次要切换的编号。
 * @returns 新的已选编号数组（不改动传入的数组）。
 */
export function toggleAll(selected: string[], ids: string[]): string[] {
  if (!ids.length) return [...selected]
  const allPicked = ids.every((id) => selected.includes(id))
  if (allPicked) return selected.filter((id) => !ids.includes(id))
  const added = ids.filter((id) => !selected.includes(id))
  return [...selected, ...added]
}

/**
 * 生成「其他项目也命中」的提示文案。
 *
 * @param input.inScope 当前项目内的命中数。
 * @param input.elsewhere 其他项目的命中数。
 * @param input.projectName 当前项目名，用于零命中时的文案。
 * @returns 提示文案；不需要提示时返回空串。
 */
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

/**
 * 汇总已选：条数、覆盖项目数与前几条用例名。
 *
 * @param selected 已选编号。
 * @param projects 全部自动化项目（用于反查标题与项目）。
 * @returns 摘要；没有已选时 count 为 0。
 */
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

/**
 * 按编号反查用例及其所属项目。
 *
 * @param projects 全部自动化项目。
 * @param caseId 用例编号。
 * @returns 命中的用例与项目；不存在时为 null。
 */
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
