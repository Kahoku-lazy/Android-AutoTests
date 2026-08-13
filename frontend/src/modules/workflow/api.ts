/**
 * 工作流工作台 API — 元素/用例 + Django workflow JSON 持久化
 */
import client from '@/shared/api-client'

/** 列出元素管理中的页面树 */
export function listPages() {
  return client.get('/elements/pages')
}

/** 列出某页下的元素 */
export function listPageElements(pageId, filter = 'all') {
  return client.get(`/elements/pages/${pageId}/items`, { params: { filter } })
}

/** 列出 Web 元素分组（项目管理） */
export function listWebGroups() {
  return client.get('/elements/web-groups')
}

/** 列出某分组下的 Web 元素 */
export function listWebGroupElements(groupId) {
  return client.get('/elements/web', { params: { group_id: groupId } })
}

/** 用例列表 */
export function listDefinitions(directoryId?: string | null) {
  const params = directoryId ? { directory_id: directoryId } : {}
  return client.get('/cases/definitions', { params })
}

/** 用例详情 */
export function getDefinition(id) {
  return client.get(`/cases/definitions/${id}`)
}

/** 创建/更新用例（与 CaseEditor 同一 upsert） */
export function saveDefinition(form) {
  return client.post('/cases/definitions', form)
}

/** 用例目录 */
export function fetchDirectories() {
  return client.get('/cases/directories')
}

// ── Workflow 目录 / JSON 文档 ──

export function listWorkflowDirectories() {
  return client.get('/workflow/directories')
}

export function createWorkflowDirectory(payload) {
  return client.post('/workflow/directories/create', payload)
}

export function updateWorkflowDirectory(dirId, payload) {
  return client.post(`/workflow/directories/${dirId}`, { action: 'update', ...payload })
}

export function deleteWorkflowDirectory(dirId) {
  return client.post(`/workflow/directories/${dirId}`, { action: 'delete' })
}

export function listWorkflowDocuments(params = {}) {
  return client.get('/workflow/documents', { params })
}

export function getWorkflowDocument(docId) {
  return client.get(`/workflow/documents/${encodeURIComponent(docId)}`)
}

/** 创建（无 doc_id）或更新（带 doc_id） */
export function saveWorkflowDocument(payload) {
  return client.post('/workflow/documents/create', payload)
}

export function updateWorkflowDocument(docId, payload) {
  return client.put(`/workflow/documents/${encodeURIComponent(docId)}`, payload)
}

export function deleteWorkflowDocument(docId) {
  return client.delete(`/workflow/documents/${encodeURIComponent(docId)}`)
}

/** 导入 envelope；overwrite=true 覆盖同 doc_id */
export function importWorkflowDocument(envelope, { overwrite = false } = {}) {
  return client.post('/workflow/documents/import', { ...envelope, overwrite }, {
    params: { overwrite: overwrite ? 1 : 0 },
  })
}

export function exportWorkflowDocument(docId) {
  return client.get(`/workflow/documents/${encodeURIComponent(docId)}/export`)
}

export function moveWorkflowDocument(docId, directoryId) {
  return client.post(`/workflow/documents/${encodeURIComponent(docId)}/move`, {
    directory_id: directoryId,
  })
}

export function moveWorkflowDirectory(dirId, parentId) {
  return client.post(`/workflow/directories/${dirId}/move`, {
    parent_id: parentId,
  })
}
