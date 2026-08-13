/**
 * [P0] 必测 — element-locator API 端点封装（表驱动，mock api-client，不断真网络）
 * 目录：tests/element-locator/p0/
 *
 * api.ts 37 个端点函数：断言 client 方法、URL、body 透传，且恰好调用一次。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import client from '@/shared/api-client'
import * as elApi from '@/modules/element-locator/api'

vi.mock('@/shared/api-client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

type ClientMethod = 'get' | 'post' | 'put' | 'delete'

interface ApiCase {
  /** 用例名：场景 + 全角冒号 + 预期 */
  name: string
  invoke: () => unknown
  method: ClientMethod
  url: string
  /** 调用带第二参数（body/params）时置 true，表内只断言 URL 与调用次数 */
  hasPayload?: boolean
}

const cases: ApiCase[] = [
  // ── Pages ──
  { name: 'apiPages：GET /elements/pages', invoke: () => elApi.apiPages(), method: 'get', url: '/elements/pages' },
  { name: 'apiUpdatePage：PUT /elements/pages/:id', invoke: () => elApi.apiUpdatePage(1, '新标签'), method: 'put', url: '/elements/pages/1', hasPayload: true },
  { name: 'apiPageItems：GET /elements/pages/:id/items', invoke: () => elApi.apiPageItems(1, 'all'), method: 'get', url: '/elements/pages/1/items', hasPayload: true },
  // ── Elements ──
  { name: 'apiUpdateElement：PUT /elements/items/:id', invoke: () => elApi.apiUpdateElement(1, { type: 'x' }), method: 'put', url: '/elements/items/1', hasPayload: true },
  // ── Flows ──
  { name: 'apiFlows：GET /elements/flows', invoke: () => elApi.apiFlows(), method: 'get', url: '/elements/flows' },
  { name: 'apiCreateFlow：POST /elements/flows', invoke: () => elApi.apiCreateFlow({ name: 'f1' }), method: 'post', url: '/elements/flows', hasPayload: true },
  { name: 'apiDeleteFlow：DELETE /elements/flows/:id', invoke: () => elApi.apiDeleteFlow(1), method: 'delete', url: '/elements/flows/1' },
  // ── Element Manager ──
  { name: 'apiGetPages：GET /elements/pages', invoke: () => elApi.apiGetPages(), method: 'get', url: '/elements/pages' },
  { name: 'apiCreatePage：POST /elements/pages/create', invoke: () => elApi.apiCreatePage({ label: 'p1' }), method: 'post', url: '/elements/pages/create', hasPayload: true },
  { name: 'apiDeletePage：DELETE /elements/pages/:id', invoke: () => elApi.apiDeletePage(1), method: 'delete', url: '/elements/pages/1' },
  { name: 'apiGetPageElements：GET /elements/pages/:pid/items', invoke: () => elApi.apiGetPageElements(1), method: 'get', url: '/elements/pages/1/items' },
  { name: 'apiAddElementToPage：POST /elements/pages/:pid/elements', invoke: () => elApi.apiAddElementToPage(1, { type: 'x' }), method: 'post', url: '/elements/pages/1/elements', hasPayload: true },
  { name: 'apiBatchAddElementsToPage：POST /elements/pages/:pid/elements/batch', invoke: () => elApi.apiBatchAddElementsToPage(1, [{ type: 'x' }], 'append'), method: 'post', url: '/elements/pages/1/elements/batch', hasPayload: true },
  { name: 'apiClearAll：POST /elements/pages/clear', invoke: () => elApi.apiClearAll([1]), method: 'post', url: '/elements/pages/clear', hasPayload: true },
  { name: 'apiBatchMovePages：POST /elements/pages/batch-move', invoke: () => elApi.apiBatchMovePages([1, 2], 5), method: 'post', url: '/elements/pages/batch-move', hasPayload: true },
  // ── Web element management ──
  { name: 'apiListWebElements：GET /elements/web', invoke: () => elApi.apiListWebElements(), method: 'get', url: '/elements/web', hasPayload: true },
  { name: 'apiCreateWebElement：POST /elements/web/create', invoke: () => elApi.apiCreateWebElement({ type: 'x' }), method: 'post', url: '/elements/web/create', hasPayload: true },
  { name: 'apiUpdateWebElement：PUT /elements/web/:id', invoke: () => elApi.apiUpdateWebElement(1, { type: 'y' }), method: 'put', url: '/elements/web/1', hasPayload: true },
  { name: 'apiDeleteWebElement：DELETE /elements/web/:id', invoke: () => elApi.apiDeleteWebElement(1), method: 'delete', url: '/elements/web/1' },
  { name: 'apiBatchImportWebElements：POST /elements/web/batch', invoke: () => elApi.apiBatchImportWebElements([{ type: 'x' }]), method: 'post', url: '/elements/web/batch', hasPayload: true },
  // ── Web group management ──
  { name: 'apiListWebGroups：GET /elements/web-groups', invoke: () => elApi.apiListWebGroups(), method: 'get', url: '/elements/web-groups' },
  { name: 'apiCreateWebGroup：POST /elements/web-groups/create', invoke: () => elApi.apiCreateWebGroup({ name: 'g1' }), method: 'post', url: '/elements/web-groups/create', hasPayload: true },
  { name: 'apiUpdateWebGroup：PUT /elements/web-groups/:id', invoke: () => elApi.apiUpdateWebGroup(1, { name: 'g2' }), method: 'put', url: '/elements/web-groups/1', hasPayload: true },
  { name: 'apiDeleteWebGroup：DELETE /elements/web-groups/:id', invoke: () => elApi.apiDeleteWebGroup(1), method: 'delete', url: '/elements/web-groups/1' },
  { name: 'apiBatchMoveWebGroups：POST /elements/web-groups/batch-move', invoke: () => elApi.apiBatchMoveWebGroups([1, 2], 5), method: 'post', url: '/elements/web-groups/batch-move', hasPayload: true },
  // ── API group management ──
  { name: 'apiListApiGroups：GET /elements/api-groups', invoke: () => elApi.apiListApiGroups(), method: 'get', url: '/elements/api-groups' },
  { name: 'apiCreateApiGroup：POST /elements/api-groups/create', invoke: () => elApi.apiCreateApiGroup({ name: 'g1' }), method: 'post', url: '/elements/api-groups/create', hasPayload: true },
  { name: 'apiUpdateApiGroup：PUT /elements/api-groups/:id', invoke: () => elApi.apiUpdateApiGroup(1, { name: 'g2' }), method: 'put', url: '/elements/api-groups/1', hasPayload: true },
  { name: 'apiDeleteApiGroup：DELETE /elements/api-groups/:id', invoke: () => elApi.apiDeleteApiGroup(1), method: 'delete', url: '/elements/api-groups/1' },
  { name: 'apiBatchMoveApiGroups：POST /elements/api-groups/batch-move', invoke: () => elApi.apiBatchMoveApiGroups([1, 2], 5), method: 'post', url: '/elements/api-groups/batch-move', hasPayload: true },
  // ── API endpoints ──
  { name: 'apiListApiEndpoints：GET /elements/api-endpoints', invoke: () => elApi.apiListApiEndpoints(), method: 'get', url: '/elements/api-endpoints', hasPayload: true },
  { name: 'apiCreateApiEndpoint：POST /elements/api-endpoints/create', invoke: () => elApi.apiCreateApiEndpoint({ path: '/x' }), method: 'post', url: '/elements/api-endpoints/create', hasPayload: true },
  { name: 'apiUpdateApiEndpoint：PUT /elements/api-endpoints/:id', invoke: () => elApi.apiUpdateApiEndpoint(1, { path: '/y' }), method: 'put', url: '/elements/api-endpoints/1', hasPayload: true },
  { name: 'apiDeleteApiEndpoint：DELETE /elements/api-endpoints/:id', invoke: () => elApi.apiDeleteApiEndpoint(1), method: 'delete', url: '/elements/api-endpoints/1' },
  // ── Web page flows ──
  { name: 'apiListWebFlows：GET /elements/web-flows', invoke: () => elApi.apiListWebFlows(), method: 'get', url: '/elements/web-flows' },
  { name: 'apiCreateWebFlow：POST /elements/web-flows', invoke: () => elApi.apiCreateWebFlow({ name: 'wf1' }), method: 'post', url: '/elements/web-flows', hasPayload: true },
  { name: 'apiDeleteWebFlow：DELETE /elements/web-flows/:id', invoke: () => elApi.apiDeleteWebFlow(1), method: 'delete', url: '/elements/web-flows/1' },
]

describe('[P0] element-locator api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it.each(cases)('$name，且恰好调用一次对应 client 方法', ({ invoke, method, url, hasPayload }) => {
    invoke()

    if (hasPayload) {
      expect(client[method]).toHaveBeenCalledWith(url, expect.anything())
    } else {
      expect(client[method]).toHaveBeenCalledWith(url)
    }
    expect(client[method]).toHaveBeenCalledTimes(1)
  })

  // ── 重点：三组 apiBatchMove* 的 parent_id 归一化 ──

  it('apiBatchMovePages：parent_id 为数字时原样透传 body', () => {
    elApi.apiBatchMovePages([1, 2], 5)

    expect(client.post).toHaveBeenCalledWith('/elements/pages/batch-move', {
      page_ids: [1, 2],
      parent_id: 5,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiBatchMovePages：parent_id 为 null 时显式归一化为 null', () => {
    elApi.apiBatchMovePages([1, 2], null)

    expect(client.post).toHaveBeenCalledWith('/elements/pages/batch-move', {
      page_ids: [1, 2],
      parent_id: null,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiBatchMoveWebGroups：parent_id 为数字时原样透传 body', () => {
    elApi.apiBatchMoveWebGroups([1, 2], 5)

    expect(client.post).toHaveBeenCalledWith('/elements/web-groups/batch-move', {
      group_ids: [1, 2],
      parent_id: 5,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiBatchMoveWebGroups：parent_id 为 null 时显式归一化为 null', () => {
    elApi.apiBatchMoveWebGroups([1, 2], null)

    expect(client.post).toHaveBeenCalledWith('/elements/web-groups/batch-move', {
      group_ids: [1, 2],
      parent_id: null,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiBatchMoveApiGroups：parent_id 为数字时原样透传 body', () => {
    elApi.apiBatchMoveApiGroups([1, 2], 5)

    expect(client.post).toHaveBeenCalledWith('/elements/api-groups/batch-move', {
      group_ids: [1, 2],
      parent_id: 5,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiBatchMoveApiGroups：parent_id 为 null 时显式归一化为 null', () => {
    elApi.apiBatchMoveApiGroups([1, 2], null)

    expect(client.post).toHaveBeenCalledWith('/elements/api-groups/batch-move', {
      group_ids: [1, 2],
      parent_id: null,
    })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  // ── 重点：apiClearAll 有/无 ids 两种 body ──

  it('apiClearAll：无 ids 时发送空 body', () => {
    elApi.apiClearAll()

    expect(client.post).toHaveBeenCalledWith('/elements/pages/clear', {})
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  it('apiClearAll：带 ids 时归一化为 page_ids 字段', () => {
    elApi.apiClearAll([1, 2])

    expect(client.post).toHaveBeenCalledWith('/elements/pages/clear', { page_ids: [1, 2] })
    expect(client.post).toHaveBeenCalledTimes(1)
  })

  // ── 重点：apiListWebElements params 透传 ──

  it('apiListWebElements：params 透传到 query', () => {
    elApi.apiListWebElements({ type: 'x', page: 2 })

    expect(client.get).toHaveBeenCalledWith('/elements/web', { params: { type: 'x', page: 2 } })
    expect(client.get).toHaveBeenCalledTimes(1)
  })
})
