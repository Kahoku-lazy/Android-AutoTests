/**
 * [P0] 必测 — 设备检查器 store 的失败呈现、状态复位与分层视图口径
 * 目录：tests/device-inspector/p0/
 *
 * 覆盖四件“界面与真实状态不一致”的缺陷：
 *  1. 失败原因取自后端 message（经共享 formatApiError 净化），而不是通用文案；
 *  2. 「重试」按失败来源重发请求，而不是只清提示；
 *  3. 删除当前展示的快照后，分层数据与选中元素一起复位；
 *  4. 分层视图口径：默认选中第一个非空分组、分组切换只改本地范围、
 *     降级来源如实透出、冻结入口不发请求。
 */
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
}))
vi.mock('@/modules/device-inspector/api', () => ({
  apiCapture: vi.fn(),
  apiGetSnapshots: vi.fn(),
  apiGetLayers: vi.fn(),
  apiDeleteSnapshot: vi.fn(),
  apiClearSnapshots: vi.fn(),
  apiSaveToElements: vi.fn(),
  apiGetPageView: vi.fn(),
  apiGetDevices: vi.fn(),
}))

import * as inspectorApi from '@/modules/device-inspector/api'
import { useElementStore } from '@/modules/device-inspector/store'

/** 构造 axios 风格的失败对象（后端 4xx 经 EnvelopeJSONRenderer 包成 {status:false,message}） */
function apiFailure(status: number, message: string) {
  return { response: { status, data: { status: false, message } } }
}

function ok<T>(data: T) {
  return { data: { status: true, data } }
}

/** 造一条分层元素（字段与后端 element 条目一致） */
function layerElement(seq: number, level1: string, level2: string | null, extra: Record<string, unknown> = {}) {
  return {
    seq,
    level1,
    level2,
    content_kind: level2 || level1,
    class_name: 'android.widget.TextView',
    class_simple: 'TextView',
    resource_id: '',
    text: '',
    content_desc: '',
    index_attr: '0',
    depth: 1,
    kept_in_snapshot: true,
    coords: { x: 0, y: seq * 10, w: 10, h: 10, cx: 5, cy: seq * 10 + 5, bounds: '[0,0][10,10]' },
    flags: {
      clickable: false, long_clickable: false, scrollable: false, checkable: false,
      checked: false, enabled: true, focusable: false,
    },
    primary: { xpath: '', type: '', count: 0, stable: false },
    ...extra,
  }
}

/** 造分层响应：布局容器 1 个、内容控件文本 2 个（默认应选中第一个非空分组＝布局容器） */
function layersPayload(overrides: Record<string, unknown> = {}) {
  return {
    snapshot_id: 7,
    source: 'index',
    package: 'com.demo',
    activity: '.Main',
    screen: { w: 1080, h: 2340 },
    screenshot_path: 'inspector/shots/capture_x.png',
    summary: {
      total: 3,
      groups: [
        { key: 'layout_container', name: '布局容器', level: 1, count: 1, kept: 1, stable_primary: 0, clickable: 0, scrollable: 0, children: [] },
        { key: 'scroll_collection', name: '滚动·集合容器', level: 1, count: 0, kept: 0, stable_primary: 0, clickable: 0, scrollable: 0, children: [] },
        {
          key: 'content_widget', name: '内容控件', level: 1, count: 2, kept: 2, stable_primary: 0, clickable: 0, scrollable: 0,
          children: [
            { key: 'text', name: '文本', level: 2, count: 2, kept: 2, stable_primary: 0, clickable: 0, scrollable: 0 },
            { key: 'icon', name: '图标', level: 2, count: 0, kept: 0, stable_primary: 0, clickable: 0, scrollable: 0 },
            { key: 'other', name: '其它', level: 2, count: 0, kept: 0, stable_primary: 0, clickable: 0, scrollable: 0 },
          ],
        },
        { key: 'unclassified', name: '其它（不属于以上三类的）', level: 1, count: 0, kept: 0, stable_primary: 0, clickable: 0, scrollable: 0, children: [] },
      ],
    },
    total_matched: 3,
    offset: 0,
    limit: 100,
    elements: [
      layerElement(1, 'layout_container', null, { class_simple: 'FrameLayout', kept_in_snapshot: false }),
      layerElement(2, 'content_widget', 'text', { text: '设备' }),
      layerElement(3, 'content_widget', 'text', { text: '设置' }),
    ],
    ...overrides,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(inspectorApi.apiGetDevices).mockResolvedValue(ok({ devices: [] }) as never)
  vi.mocked(inspectorApi.apiGetSnapshots).mockResolvedValue(ok({ items: [], total: 0 }) as never)
})

describe('设备检查器 store', () => {
  it('抓取失败时提示后端返回的原因，而不是通用文案', async () => {
    const store = useElementStore()
    store.captureSerial = 'R5CT62RH88F'
    vi.mocked(inspectorApi.apiCapture).mockRejectedValue(
      apiFailure(409, '设备正被执行引擎占用（runner-1），请等待执行完毕') as never,
    )

    await store.capture()

    expect(ElMessage.error).toHaveBeenCalledWith('设备正被执行引擎占用（runner-1），请等待执行完毕')
    expect(store.error).toEqual({
      message: '设备正被执行引擎占用（runner-1），请等待执行完毕',
      source: 'capture',
    })
  })

  it('「重试」按失败来源重发请求，并在成功后撤掉错误', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetSnapshots).mockRejectedValueOnce(
      apiFailure(500, '快照列表加载失败') as never,
    )

    await store.fetchSnapshots()
    expect(store.error?.source).toBe('snapshots')

    vi.mocked(inspectorApi.apiGetSnapshots).mockResolvedValueOnce(
      ok({ items: [{ id: 1 }], total: 1 }) as never,
    )
    await store.retry()

    expect(inspectorApi.apiGetSnapshots).toHaveBeenCalledTimes(2)
    expect(store.error).toBeNull()
  })

  it('分层数据加载失败时「重试」重发分层请求', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockRejectedValueOnce(apiFailure(500, '元素数据加载失败') as never)

    await store.fetchLayers(7)
    expect(store.error?.source).toBe('layers')

    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)
    await store.retry()

    expect(inspectorApi.apiGetLayers).toHaveBeenCalledTimes(2)
    expect(store.elements).toHaveLength(3)
    expect(store.error).toBeNull()
  })

  it('删除当前展示的快照后，分层数据与选中元素一起复位', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)

    await store.viewSnapshot(7)
    store.selectElement(store.elements[1])
    expect(store.groupElements).toHaveLength(1)
    expect(store.selected).not.toBeNull()

    vi.mocked(inspectorApi.apiDeleteSnapshot).mockResolvedValueOnce({ data: { status: true } } as never)
    await store.deleteSnapshot(7)

    expect(store.snapshot).toBeNull()
    expect(store.layers).toBeNull()
    expect(store.elements).toHaveLength(0)
    expect(store.selected).toBeNull()
  })

  it('默认选中第一个非空分组，切分组只改本地展示范围（不发请求）', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)

    await store.fetchLayers(7)
    expect(inspectorApi.apiGetLayers).toHaveBeenCalledTimes(1)

    // 布局容器有 1 个元素，是顺序上的第一个非空分组
    expect(store.activeGroupId).toBe('layout_container')
    expect(store.groupElements).toHaveLength(1)
    expect(store.groupElements[0].kept_in_snapshot).toBe(false)

    store.activeGroupId = 'content_widget/text'
    expect(store.groupElements).toHaveLength(2)
    expect(inspectorApi.apiGetLayers).toHaveBeenCalledTimes(1)

    // 分组徽标恒为全量计数，切分组不变
    expect(store.groupBadges.map(g => g.count)).toEqual([1, 0, 2, 0, 0])
  })

  it('降级来源如实透出（历史快照无全量索引）', async () => {
    const store = useElementStore()
    // 降级集只有保留元素（索引缺失，后端不会给出被裁元素）
    const legacy = layersPayload({
      source: 'legacy',
      elements: [
        layerElement(1, 'layout_container', null, { class_simple: 'FrameLayout' }),
        layerElement(2, 'content_widget', 'text', { text: '设备' }),
      ],
    })
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(legacy) as never)

    await store.fetchLayers(7)

    expect(store.layerSource).toBe('legacy')
    expect(store.elements.every(e => e.kept_in_snapshot)).toBe(true)
  })

  it('冻结入口不发请求：保存与已保存页面回看都只提示原因', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)
    await store.fetchLayers(7)

    const saved = await store.saveToElements({ pageLabel: '页面', folderPath: '' })
    const page = await store.viewSavedPage(3)

    expect(saved).toBeNull()
    expect(page).toBeNull()
    expect(inspectorApi.apiSaveToElements).not.toHaveBeenCalled()
    expect(inspectorApi.apiGetPageView).not.toHaveBeenCalled()
    expect(ElMessage.warning).toHaveBeenCalledTimes(2)
  })

  it('一键清空成功后列表与分层状态一起复位', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)
    await store.viewSnapshot(7)
    store.selectElement(store.elements[1])
    expect(store.snapshot).not.toBeNull()

    vi.mocked(inspectorApi.apiClearSnapshots).mockResolvedValueOnce(ok({ deleted: 12 }) as never)
    const deleted = await store.clearSnapshots()

    expect(deleted).toBe(12)
    expect(inspectorApi.apiClearSnapshots).toHaveBeenCalledTimes(1)
    expect(store.snapshot).toBeNull()
    expect(store.layers).toBeNull()
    expect(store.elements).toHaveLength(0)
    expect(store.selected).toBeNull()
    expect(inspectorApi.apiGetSnapshots).toHaveBeenCalled()
  })

  it('一键清空失败时呈现后端原因，且不清空本地状态', async () => {
    const store = useElementStore()
    vi.mocked(inspectorApi.apiGetLayers).mockResolvedValueOnce(ok(layersPayload()) as never)
    await store.viewSnapshot(7)

    vi.mocked(inspectorApi.apiClearSnapshots).mockRejectedValueOnce(apiFailure(500, '清空失败') as never)
    const deleted = await store.clearSnapshots()

    expect(deleted).toBeNull()
    expect(ElMessage.error).toHaveBeenCalledWith('清空失败')
    expect(store.layers).not.toBeNull()
    expect(store.snapshot).not.toBeNull()
  })
})