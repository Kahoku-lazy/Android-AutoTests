/** element-locator API client functions */
import client from '@/shared/api-client'

// ── Element dump & actions ──

export function apiDump()         { return client.post('/elements/dump', {}) }
export function apiAction(a,x,y)  { return client.post('/elements/action',{action:a,x,y}) }
export function apiInput(t,x,y,c) { return client.post('/elements/action',{action:'input',text:t,x,y,clear_first:c}) }

// ── Pages ──

export function apiPages()        { return client.get('/elements/pages') }
export function apiUpdatePage(id,label) { return client.put(`/elements/pages/${id}`,{label}) }
export function apiPageItems(id,f) { return client.get(`/elements/pages/${id}/items`,{params:{filter:f}}) }

// ── Elements ──

export function apiUpdateElement(id,d) { return client.put(`/elements/items/${id}`,d) }

// ── Flows ──

export function apiFlows()        { return client.get('/elements/flows') }
export function apiCreateFlow(f)  { return client.post('/elements/flows',f) }
export function apiDeleteFlow(id) { return client.delete(`/elements/flows/${id}`) }

// ── Device integration (v2) ──

export function apiGetDevices()           { return client.get('/devices') }
export function apiActivateDevice(s)      { return client.post(`/devices/${s}/activate`) }
export function apiGetDeviceInfo()        { return client.get('/elements/device-info') }
export function apiGetScreenshot()        { return client.get('/elements/screenshot') }

// ── Observe-mode connect/disconnect (manual device control) ──

export function apiConnectObserve(serial) {
  return client.post(`/devices/${serial}`, { activate: true, mode: 'observe' })
}
export function apiDisconnectObserve(serial) {
  return client.post(`/devices/${serial}/disconnect-observe`)
}

// ── Element Manager (page & element CRUD) ──

export function apiGetPages()          { return client.get('/elements/pages') }
export function apiCreatePage(data)    { return client.post('/elements/pages/create', data) }
export function apiDeletePage(id)      { return client.delete(`/elements/pages/${id}`) }
export function apiGetPageElements(pid) { return client.get(`/elements/pages/${pid}/items`) }
export function apiAddElementToPage(pid, el) { return client.post(`/elements/pages/${pid}/elements`, el) }
export function apiBatchAddElementsToPage(pid, elements, strategy) { return client.post(`/elements/pages/${pid}/elements/batch`, { elements, strategy }) }
export function apiClearAll()          { return client.post('/elements/pages/clear') }
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
