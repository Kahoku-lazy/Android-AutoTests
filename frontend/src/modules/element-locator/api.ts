/** element-locator API client functions — persistent element repository CRUD */
import client from '@/shared/api-client'
import type { DjangoResponse } from '@/shared/api-client'
import type {
  CreatePagePayload,
  ElementWritePayload,
  LocatorProject,
  LocatorTreePayload,
  PageElementsPayload,
} from './types'

type Envelope<T> = Promise<{ data: DjangoResponse<T> }>

/** legacy 平铺响应：只取 axios 响应的 `data`（登记特例：非 {status,data} 信封） */
type FlatResponse<T> = Promise<{ data: T }>

// 路径约定：全平台 /api/ 路径以 / 结尾（见 openspec/specs/api-path-convention）。
// Web 元素与 API 接口两组封装随元素定位的 Web、API 两域整体下线而移除
// （变更 remove-element-locator-web-api）；本文件只保留 router 形式。

// ── Projects / directories（标准 {status,data} 信封）──

export function listLocatorProjects(): Envelope<LocatorProject[]> {
  return client.get<DjangoResponse<LocatorProject[]>>('/elements/projects/')
}

export function getLocatorProjectTree(code: string): Envelope<LocatorTreePayload> {
  return client.get<DjangoResponse<LocatorTreePayload>>(`/elements/projects/${code}/tree/`)
}

export function createLocatorDirectory(body: {
  project_code: string
  name: string
  parent_id?: number | null
}): Envelope<Record<string, unknown>> {
  return client.post<DjangoResponse<Record<string, unknown>>>('/elements/directories/', body)
}

export function updateLocatorDirectory(
  id: number,
  body: { name?: string; sort_order?: number },
): Envelope<Record<string, unknown>> {
  return client.patch<DjangoResponse<Record<string, unknown>>>(`/elements/directories/${id}/`, body)
}

export function deleteLocatorDirectory(id: number): Envelope<{ id: number }> {
  return client.delete<DjangoResponse<{ id: number }>>(`/elements/directories/${id}/`)
}

// ── Pages ──

export function apiPageItems(
  id: number,
  filter: string,
  limit = 500,
): FlatResponse<PageElementsPayload> {
  return client.get<PageElementsPayload>(`/elements/pages/${id}/items/`, {
    params: { filter, limit },
  })
}

// ── Elements ──

/**
 * 元素行可写字段（wire snake_case）。
 * 更新只接受 元素名称 / 文本 / 主定位 / 测试点；新增额外接受备注与去重键（resource_id / bounds）。
 */
export interface PageElementFields {
  alias?: string
  text_val?: string
  primary_xpath?: string
  notes?: string
  is_test_point?: boolean
  resource_id?: string
  bounds?: string
}

export function apiUpdateElement(
  id: number,
  data: PageElementFields,
): FlatResponse<ElementWritePayload> {
  return client.put<ElementWritePayload>(`/elements/items/${id}/`, data)
}

/** 新增一条元素行（create-only：撞同页既有的 resource-id + bounds 会返回 409） */
export function createPageElement(
  pageId: number,
  data: PageElementFields,
): FlatResponse<ElementWritePayload> {
  return client.post<ElementWritePayload>(`/elements/pages/${pageId}/elements/`, data)
}

/** 批量删除元素行（原子） */
export function batchDeleteElements(ids: number[]) {
  return client.post('/elements/items/batch-delete/', { ids })
}

// ── Page CRUD ──

export function apiCreatePage(data: {
  label: string
  directory_id?: number | null
}): FlatResponse<CreatePagePayload> {
  return client.post<CreatePagePayload>('/elements/pages/create/', data)
}

export function apiDeletePage(id: number): FlatResponse<ElementWritePayload> {
  return client.delete<ElementWritePayload>(`/elements/pages/${id}/`)
}

// ── Move ──

export interface LocatorMoveItem {
  kind: 'directory' | 'page'
  id: number
}

/** 单件拖动与批量勾选共用同一端点：items 只有 1 项时即单件移动 */
export function moveLocatorItems(body: {
  items: LocatorMoveItem[]
  parent_directory_id: number | null
}): Envelope<{ moved: number; skipped: number }> {
  return client.post<DjangoResponse<{ moved: number; skipped: number }>>(
    '/elements/batch-move/',
    body,
  )
}

/** 批量删除勾选节点；删除目录会连同其下子目录、页面与元素一并删除 */
export function deleteLocatorItems(body: {
  items: LocatorMoveItem[]
}): Envelope<{ deleted: number; pages: number; elements: number }> {
  return client.post<DjangoResponse<{ deleted: number; pages: number; elements: number }>>(
    '/elements/batch-delete/',
    body,
  )
}
