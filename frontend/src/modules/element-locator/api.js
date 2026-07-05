/** element-locator API client functions */
import client from '@/shared/api-client.js'

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

export function apiGetDevices()        { return client.get('/devices') }
export function apiActivateDevice(s)   { return client.post(`/devices/${s}/activate`) }
export function apiGetDeviceInfo()     { return client.get('/elements/device-info') }
export function apiGetScreenshot()     { return client.get('/elements/screenshot') }

// ── Element Manager (page & element CRUD) ──

export function apiGetPages()          { return client.get('/elements/pages') }
export function apiCreatePage(label)   { return client.post('/elements/pages/create', { label }) }
export function apiDeletePage(id)      { return client.delete(`/elements/pages/${id}`) }
export function apiGetPageElements(pid) { return client.get(`/elements/pages/${pid}/items`) }
export function apiAddElementToPage(pid, el) { return client.post(`/elements/pages/${pid}/elements`, el) }
export function apiClearAll()          { return client.post('/elements/pages/clear') }
