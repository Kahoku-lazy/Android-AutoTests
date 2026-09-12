/** element-locator API client functions — persistent element repository CRUD */
import client from '@/shared/api-client'
import type { DjangoResponse } from '@/shared/api-client'
import type {
  ApiEndpointDetail,
  LocatorFileKind,
  LocatorProject,
  LocatorTreePayload,
  WebElementDetail,
} from './types'

type Envelope<T> = Promise<{ data: DjangoResponse<T> }>

// ── Projects / directories / move（标准 {status,data} 信封）──

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

export function moveLocatorItem(body: {
  kind: 'directory' | LocatorFileKind
  id: number
  parent_directory_id?: number | null
}): Envelope<Record<string, unknown>> {
  return client.post<DjangoResponse<Record<string, unknown>>>('/elements/move/', body)
}

export function batchDeleteLocatorFiles(body: {
  kind: LocatorFileKind
  ids: number[]
}): Envelope<{ kind: string; deleted: number }> {
  return client.post<DjangoResponse<{ kind: string; deleted: number }>>(
    '/elements/files/batch-delete/',
    body,
  )
}

export function apiGetWebElement(id: number): Envelope<WebElementDetail> {
  return client.get<DjangoResponse<WebElementDetail>>(`/elements/web/${id}/`)
}

export function apiGetApiEndpoint(id: number): Envelope<ApiEndpointDetail> {
  return client.get<DjangoResponse<ApiEndpointDetail>>(`/elements/api-endpoints/${id}/`)
}

// ── Pages ──

export function apiPages()        { return client.get('/elements/pages') }
export function apiUpdatePage(id,label) { return client.put(`/elements/pages/${id}`,{label}) }
export function apiPageItems(id,f,limit=500) { return client.get(`/elements/pages/${id}/items`,{params:{filter:f,limit}}) }

// ── Elements ──

export function apiUpdateElement(id,d) { return client.put(`/elements/items/${id}`,d) }

// ── Flows ──

export function apiFlows()        { return client.get('/elements/flows') }
export function apiCreateFlow(f)  { return client.post('/elements/flows',f) }
export function apiDeleteFlow(id) { return client.delete(`/elements/flows/${id}`) }

// ── Element Manager (page & element CRUD) ──

export function apiGetPages()          { return client.get('/elements/pages') }
export function apiCreatePage(data)    { return client.post('/elements/pages/create', data) }
export function apiDeletePage(id)      { return client.delete(`/elements/pages/${id}`) }
export function apiGetPageElements(pid) { return client.get(`/elements/pages/${pid}/items`) }
export function apiAddElementToPage(pid, el) { return client.post(`/elements/pages/${pid}/elements`, el) }
export function apiBatchAddElementsToPage(pid, elements, strategy) { return client.post(`/elements/pages/${pid}/elements/batch`, { elements, strategy }) }
export function apiClearAll(ids?: (string | number)[] | null) { return client.post('/elements/pages/clear', ids ? { page_ids: ids } : {}) }
export function apiBatchMovePages(pageIds, parentId) {
  return client.post('/elements/pages/batch-move', {
    page_ids: pageIds,
    parent_id: parentId ?? null,
  })
}

// ── Web element management ──

export function apiListWebElements(params = {}) {
  return client.get('/elements/web', { params })
}

export function apiCreateWebElement(data) {
  return client.post('/elements/web/create', data)
}

export function apiUpdateWebElement(id, data) {
  return client.put(`/elements/web/${id}`, data)
}

export function apiDeleteWebElement(id) {
  return client.delete(`/elements/web/${id}`)
}

export function apiBatchImportWebElements(elements) {
  return client.post('/elements/web/batch', { elements })
}

// ── Web group management ──

export function apiListWebGroups() {
  return client.get('/elements/web-groups')
}

export function apiCreateWebGroup(data) {
  return client.post('/elements/web-groups/create', data)
}

export function apiUpdateWebGroup(id, data) {
  return client.put(`/elements/web-groups/${id}`, data)
}

export function apiDeleteWebGroup(id) {
  return client.delete(`/elements/web-groups/${id}`)
}

export function apiBatchMoveWebGroups(groupIds, parentId) {
  return client.post('/elements/web-groups/batch-move', {
    group_ids: groupIds,
    parent_id: parentId ?? null,
  })
}

// ── API group management ──

export function apiListApiGroups() {
  return client.get('/elements/api-groups')
}

export function apiCreateApiGroup(data) {
  return client.post('/elements/api-groups/create', data)
}

export function apiUpdateApiGroup(id, data) {
  return client.put(`/elements/api-groups/${id}`, data)
}

export function apiDeleteApiGroup(id) {
  return client.delete(`/elements/api-groups/${id}`)
}

export function apiBatchMoveApiGroups(groupIds, parentId) {
  return client.post('/elements/api-groups/batch-move', {
    group_ids: groupIds,
    parent_id: parentId ?? null,
  })
}

// ── API endpoints ──

export function apiListApiEndpoints(params = {}) {
  return client.get('/elements/api-endpoints', { params })
}

export function apiCreateApiEndpoint(data) {
  return client.post('/elements/api-endpoints/create', data)
}

export function apiUpdateApiEndpoint(id, data) {
  return client.put(`/elements/api-endpoints/${id}`, data)
}

export function apiDeleteApiEndpoint(id) {
  return client.delete(`/elements/api-endpoints/${id}`)
}

// ── Web page flows ──

export function apiListWebFlows() {
  return client.get('/elements/web-flows')
}
export function apiCreateWebFlow(data) {
  return client.post('/elements/web-flows', data)
}
export function apiDeleteWebFlow(id) {
  return client.delete(`/elements/web-flows/${id}`)
}
