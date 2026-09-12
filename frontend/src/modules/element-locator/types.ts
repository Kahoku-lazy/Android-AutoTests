/** element-locator 项目化类型（wire snake_case） */

export type LocatorProjectCode = 'android' | 'web' | 'api'
export type LocatorFileKind = 'page' | 'web_element' | 'api_endpoint'

export const LOCATOR_PROJECT_CODES: LocatorProjectCode[] = ['android', 'web', 'api']

export const FILE_KIND_BY_CODE: Record<LocatorProjectCode, LocatorFileKind> = {
  android: 'page',
  web: 'web_element',
  api: 'api_endpoint',
}

export const PROJECT_HINTS: Record<LocatorProjectCode, string> = {
  android: 'Android 页面与控件定位库',
  web: 'Web 页面元素定位库',
  api: 'REST API 接口定义库',
}

export const FILE_KIND_LABELS: Record<LocatorFileKind, string> = {
  page: '页面',
  web_element: 'Web 元素',
  api_endpoint: 'API 接口',
}

export const WEB_LOCATOR_TYPES = [
  { value: 'css_selector', label: 'CSS Selector' },
  { value: 'xpath', label: 'XPath' },
  { value: 'id', label: 'ID' },
  { value: 'class_name', label: 'Class Name' },
  { value: 'name', label: 'Name' },
  { value: 'tag_name', label: 'Tag Name' },
  { value: 'link_text', label: 'Link Text' },
  { value: 'partial_link_text', label: 'Partial Link Text' },
  { value: 'text', label: 'Text' },
  { value: 'test_id', label: 'Test ID' },
  { value: 'role', label: 'ARIA Role' },
  { value: 'placeholder', label: 'Placeholder' },
] as const

export const API_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] as const

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

export interface WebElementDetail {
  id: number
  name: string
  locator_type: string
  locator_value: string
  page_url?: string
  description?: string
}

export interface ApiEndpointDetail {
  id: number
  name: string
  method: string
  url: string
  description?: string
}

export function isLocatorProjectCode(value: string): value is LocatorProjectCode {
  return LOCATOR_PROJECT_CODES.includes(value as LocatorProjectCode)
}
