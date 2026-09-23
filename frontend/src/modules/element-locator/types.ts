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

// ── 页面元素（legacy 平铺响应，wire snake_case；真相源 views_page_elements._element_payload）──

/** 单条元素的 wire 形状（收敛口径：无候选 XPath、无页面截图路径） */
export interface PageElementPayload {
  id: number
  page_id: number
  alias: string
  text_val: string
  resource_id: string
  bounds: string
  seq: number
  primary_xpath: string
  primary_stable: boolean
  thumbnail_path: string
  clickable: boolean
  long_clickable: boolean
  scrollable: boolean
  checkable: boolean
  checked: boolean
  enabled: boolean
  focusable: boolean
  is_test_point: boolean
  notes: string
  created_at: string
}

/** `GET /elements/pages/{id}/items/` 的平铺响应（登记特例：非 {status,data} 信封） */
export interface PageElementsPayload {
  status: boolean
  elements?: PageElementPayload[]
  total?: number
  message?: string
}

/** 元素写入类端点的平铺响应：成功只回 status，失败带 message */
export interface ElementWritePayload {
  status: boolean
  message?: string
}

/** `POST /elements/pages/create/` 的平铺响应 */
export interface CreatePagePayload extends ElementWritePayload {
  page?: { id: number; label?: string }
}

export function isLocatorProjectCode(value: string): value is LocatorProjectCode {
  return LOCATOR_PROJECT_CODES.includes(value as LocatorProjectCode)
}
