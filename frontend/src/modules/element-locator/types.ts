/** element-locator 项目化类型（wire snake_case） */

export type LocatorProjectCode = 'android'
export type LocatorFileKind = 'page'

export const LOCATOR_PROJECT_CODES: LocatorProjectCode[] = ['android']

export const FILE_KIND_BY_CODE: Record<LocatorProjectCode, LocatorFileKind> = {
  android: 'page',
}

export const PROJECT_HINTS: Record<LocatorProjectCode, string> = {
  android: 'Android 页面与控件定位库',
}

export const FILE_KIND_LABELS: Record<LocatorFileKind, string> = {
  page: '页面',
}

export interface LocatorProject {
  id: number
  code: LocatorProjectCode
  name: string
  description: string
  file_count: number
  created_at: string
  updated_at: string
  locked: boolean
}

export interface LocatorDirNode {
  type: 'directory'
  id: number
  name: string
  sort_order: number
  children: LocatorTreeNode[]
}

export interface LocatorFileNode {
  type: 'file'
  kind: LocatorFileKind
  id: number
  name: string
  sort_order: number
}

export type LocatorTreeNode = LocatorDirNode | LocatorFileNode

export interface LocatorTreePayload {
  project: LocatorProject
  tree: LocatorTreeNode[]
}

export function isLocatorProjectCode(value: string): value is LocatorProjectCode {
  return LOCATOR_PROJECT_CODES.includes(value as LocatorProjectCode)
}
