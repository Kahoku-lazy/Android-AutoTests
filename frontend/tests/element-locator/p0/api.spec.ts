/**
 * [P0] 必测 — element-locator API 端点封装（表驱动，mock api-client，不断真网络）
 * 目录：tests/element-locator/p0/
 *
 * api.ts 现存 14 个端点函数：断言 client 方法、URL、body 透传，且恰好调用一次。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import client from '@/shared/api-client'
import * as elApi from '@/modules/element-locator/api'

vi.mock('@/shared/api-client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

type ClientMethod = 'get' | 'post' | 'put' | 'patch' | 'delete'

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
  // ── Projects / directories ──
  { name: 'listLocatorProjects：GET /elements/projects', invoke: () => elApi.listLocatorProjects(), method: 'get', url: '/elements/projects/' },
  { name: 'getLocatorProjectTree：GET /elements/projects/:code/tree', invoke: () => elApi.getLocatorProjectTree('android'), method: 'get', url: '/elements/projects/android/tree/' },
  { name: 'createLocatorDirectory：POST /elements/directories', invoke: () => elApi.createLocatorDirectory({ project_code: 'android', name: 'd1' }), method: 'post', url: '/elements/directories/', hasPayload: true },
  { name: 'updateLocatorDirectory：PATCH /elements/directories/:id', invoke: () => elApi.updateLocatorDirectory(1, { name: 'd2' }), method: 'patch', url: '/elements/directories/1/', hasPayload: true },
  { name: 'deleteLocatorDirectory：DELETE /elements/directories/:id', invoke: () => elApi.deleteLocatorDirectory(1), method: 'delete', url: '/elements/directories/1/' },
  // ── Pages ──
  { name: 'apiPageItems：GET /elements/pages/:id/items', invoke: () => elApi.apiPageItems(1, 'all'), method: 'get', url: '/elements/pages/1/items/', hasPayload: true },
  // ── Elements ──
  { name: 'apiUpdateElement：PUT /elements/items/:id', invoke: () => elApi.apiUpdateElement(1, { alias: '改后名称' }), method: 'put', url: '/elements/items/1/', hasPayload: true },
  // ── Element Manager (page CRUD) ──
  { name: 'apiGetPages：GET /elements/pages', invoke: () => elApi.apiGetPages(), method: 'get', url: '/elements/pages/' },
  { name: 'apiCreatePage：POST /elements/pages/create', invoke: () => elApi.apiCreatePage({ label: 'p1' }), method: 'post', url: '/elements/pages/create/', hasPayload: true },
  { name: 'apiDeletePage：DELETE /elements/pages/:id', invoke: () => elApi.apiDeletePage(1), method: 'delete', url: '/elements/pages/1/' },
  // ── Move ──
  { name: 'moveLocatorItems：POST /elements/batch-move', invoke: () => elApi.moveLocatorItems({ items: [{ kind: 'page', id: 1 }], parent_directory_id: 2 }), method: 'post', url: '/elements/batch-move/', hasPayload: true },
  { name: 'deleteLocatorItems：POST /elements/batch-delete', invoke: () => elApi.deleteLocatorItems({ items: [{ kind: 'directory', id: 3 }] }), method: 'post', url: '/elements/batch-delete/', hasPayload: true },
  { name: 'createPageElement：POST /elements/pages/:id/elements', invoke: () => elApi.createPageElement(1, { alias: 'x' }), method: 'post', url: '/elements/pages/1/elements/', hasPayload: true },
  { name: 'batchDeleteElements：POST /elements/items/batch-delete', invoke: () => elApi.batchDeleteElements([1, 2]), method: 'post', url: '/elements/items/batch-delete/', hasPayload: true },
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
})

describe('[P0] element-locator 批量移动', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('moveLocatorItems 透传 items 与「项目根」目标（parent_directory_id 为 null）', () => {
    const body = { items: [{ kind: 'page' as const, id: 7 }], parent_directory_id: null }

    elApi.moveLocatorItems(body)

    expect(client.post).toHaveBeenCalledWith('/elements/batch-move/', body)
  })
})

describe('[P0] element-locator 批量删除', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deleteLocatorItems 透传 items（目录与页面可混合）', () => {
    const body = {
      items: [
        { kind: 'directory' as const, id: 3 },
        { kind: 'page' as const, id: 9 },
      ],
    }

    elApi.deleteLocatorItems(body)

    expect(client.post).toHaveBeenCalledWith('/elements/batch-delete/', body)
  })
})

describe('[P0] element-locator 元素行增删', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('createPageElement 透传字段到页面元素端点', () => {
    const body = { alias: '新元素', resource_id: 'com.demo:id/x' }

    elApi.createPageElement(7, body)

    expect(client.post).toHaveBeenCalledWith('/elements/pages/7/elements/', body)
  })

  it('batchDeleteElements 以 ids 数组提交', () => {
    elApi.batchDeleteElements([3, 5])

    expect(client.post).toHaveBeenCalledWith('/elements/items/batch-delete/', { ids: [3, 5] })
  })
})
