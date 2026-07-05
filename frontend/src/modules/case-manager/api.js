/**
 * case-manager API — 用例管理模块
 */
import client from '@/shared/api-client.js'

// ── 用例定义 ──

export function listDefinitions() {
  return client.get('/cases/definitions')
}

export function getDefinition(id) {
  return client.get(`/cases/definitions/${id}`)
}

export function saveDefinition(form) {
  return client.post('/cases/definitions', form)
}

export function deleteDefinition(id) {
  return client.delete(`/cases/definitions/${id}`)
}

// ── 设备（跨模块，调试用）──

export function listDevices() {
  return client.get('/devices')
}

// ── 元素库（跨模块，步骤编辑器用）──

export function listPages() {
  return client.get('/elements/pages')
}

export function getPageElements(pageId) {
  return client.get(`/elements/pages/${pageId}/items`)
}

// ── 单步调试（跨模块）──

export function runStep(params) {
  return client.post('/runner/run-step', params)
}
