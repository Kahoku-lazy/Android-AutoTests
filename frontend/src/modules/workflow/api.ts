/**
 * 工作流工作台 API — 原型 + 目录/文档 + 元素素材
 */
import client from '@/shared/api-client'
import type { DjangoResponse } from '@/shared/api-client'

type Envelope<T> = Promise<{ data: DjangoResponse<T> }>

export interface WorkflowPrototype {
  id: number
  name: string
  description: string
  doc_count: number
  created_at?: string
  updated_at?: string
}

export interface WorkflowDirectoryRow {
  id: number
  name: string
  parent_id: number | null
  created_at?: string
  updated_at?: string
}

export interface WorkflowDocumentRow {
  doc_id: string
  title: string
  doc_type: string
  directory_id: number | null
  description?: string
  config?: unknown
  created_at?: string
  updated_at?: string
}

/** 列出元素管理中的页面树 */
export function listPages() {
  return client.get('/elements/pages/')
}

/** 列出某页下的元素 */
export function listPageElements(pageId, filter = 'all') {
  return client.get(`/elements/pages/${pageId}/items/`, { params: { filter } })
}

// ── 原型 ──

export function listWorkflowPrototypes(): Envelope<WorkflowPrototype[]> {
  return client.get('/workflow/prototypes/')
}

export function getWorkflowPrototype(id: number): Envelope<WorkflowPrototype> {
  return client.get(`/workflow/prototypes/${id}/`)
}

export function createWorkflowPrototype(payload) {
  return client.post('/workflow/prototypes/', payload)
}

export function updateWorkflowPrototype(id, payload) {
  return client.patch(`/workflow/prototypes/${id}/`, payload)
}

export function deleteWorkflowPrototype(id) {
  return client.delete(`/workflow/prototypes/${id}/`)
}

// ── Workflow 目录 / JSON 文档 ──

export function listWorkflowDirectories(params = {}): Envelope<{
  directories: WorkflowDirectoryRow[]
  tree: unknown[]
}> {
  return client.get('/workflow/directories/', { params })
}

export function createWorkflowDirectory(payload) {
  return client.post('/workflow/directories/', payload)
}

export function updateWorkflowDirectory(dirId, payload) {
  return client.patch(`/workflow/directories/${dirId}/`, payload)
}

export function deleteWorkflowDirectory(dirId) {
  return client.delete(`/workflow/directories/${dirId}/`)
}

export function listWorkflowDocuments(params = {}): Envelope<WorkflowDocumentRow[]> {
  return client.get('/workflow/documents/', { params })
}

export function getWorkflowDocument(docId: string): Envelope<WorkflowDocumentRow> {
  return client.get(`/workflow/documents/${encodeURIComponent(docId)}/`)
}

/** 创建文档（集合路由）；更新走 updateWorkflowDocument */
export function saveWorkflowDocument(payload) {
  return client.post('/workflow/documents/', payload)
}

export function updateWorkflowDocument(docId, payload) {
  return client.put(`/workflow/documents/${encodeURIComponent(docId)}/`, payload)
}

export function deleteWorkflowDocument(docId) {
  return client.delete(`/workflow/documents/${encodeURIComponent(docId)}/`)
}

/** 导入 envelope（router 动作路由）；overwrite=true 覆盖同 doc_id */
export function importWorkflowDocument(envelope, { overwrite = false } = {}) {
  return client.post('/workflow/documents/import/', envelope, {
    params: { overwrite: overwrite ? 1 : 0 },
  })
}

export function exportWorkflowDocument(
  docId: string,
): Envelope<{ envelope: Record<string, unknown> }> {
  return client.get(`/workflow/documents/${encodeURIComponent(docId)}/export/`)
}

export function moveWorkflowDocument(docId, directoryId) {
  return client.post(`/workflow/documents/${encodeURIComponent(docId)}/move/`, {
    directory_id: directoryId,
  })
}

export function moveWorkflowDirectory(dirId, parentId) {
  return client.post(`/workflow/directories/${dirId}/move/`, {
    parent_id: parentId,
  })
}
