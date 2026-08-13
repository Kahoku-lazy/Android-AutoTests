/**
 * [P0] 必测 — 元素定位页面树 composable（树构建 / 坏 JSON 降级 / 拖拽环检测 / 自动加载）
 * 目录：tests/element-locator/p0/
 *
 * buildPageTree / isDescendantOf 未导出，经返回的 pageTree / allowDrop 测可观察行为；
 * onMounted 自动 loadPages 用 mountComposable 挂载触发。
 * 统一 mock element-plus、模块 api、event-bus，不断真网络。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as elApi from '@/modules/element-locator/api'
import { useElementTree } from '@/modules/element-locator/composables/useElementTree'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() }, ElMessageBox: { confirm: vi.fn() } }))
vi.mock('@/modules/element-locator/api', () => ({ apiGetPages: vi.fn(), apiCreatePage: vi.fn(), apiUpdatePage: vi.fn(), apiDeletePage: vi.fn(), apiGetPageElements: vi.fn(), apiBatchMovePages: vi.fn(), apiClearAll: vi.fn() }))
vi.mock('@/shared/event-bus', () => ({ bus: { on: vi.fn(), off: vi.fn(), emit: vi.fn() } }))

describe('[P0] element-locator useElementTree', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('buildPageTree：扁平列表转为嵌套树，孤儿归结到根', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({
      data: {
        status: true,
        pages: [
          { id: 1, label: '目录A', is_folder: true, parent_id: null },
          { id: 2, label: '页面B', is_folder: false, parent_id: 1 },
          { id: 3, label: '孤儿C', is_folder: false, parent_id: 99 },
        ],
      },
    } as never)
    const { result, wrapper } = await mountComposable(() => useElementTree())
    await flushPromises()

    expect(result.pageTree.value).toHaveLength(2)
    expect(result.pageTree.value[0].id).toBe(1)
    expect(result.pageTree.value[0].children).toHaveLength(1)
    expect(result.pageTree.value[0].children[0].id).toBe(2)
    expect(result.pageTree.value[1].id).toBe(3) // parent_id=99 不存在 → 归根
    expect(result.pageTree.value[1].children).toHaveLength(0)
    wrapper.unmount()
  })

  it('selectPage：xpath_candidates 坏 JSON 降级为 []，不抛异常', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({ data: { status: true, pages: [] } } as never)
    vi.mocked(elApi.apiGetPageElements).mockResolvedValue({
      data: {
        status: true,
        elements: [
          { id: 1, xpath_candidates: '{bad json' },
          { id: 2, xpath_candidates: '[{"xpath":"//a[1]"}]' },
        ],
      },
    } as never)
    const { result, wrapper } = await mountComposable(() => useElementTree())
    await flushPromises()

    await result.selectPage({ id: 9, label: '页9' })
    expect(result.selectedPage.value.id).toBe(9)
    expect(result.elements.value).toHaveLength(2)
    expect(result.elements.value[0]._xpaths).toEqual([]) // 坏 JSON → []
    expect(result.elements.value[0]._first_xpath).toBe('') // 坏 JSON → ''
    expect(result.elements.value[1]._first_xpath).toBe('//a[1]') // 正常解析对照
    wrapper.unmount()
  })

  it('拖拽环检测：父目录拖进自身子目录返回 false，未调 apiBatchMovePages', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({
      data: {
        status: true,
        pages: [
          { id: 1, label: '目录A', is_folder: true, parent_id: null },
          { id: 2, label: '子目录B', is_folder: true, parent_id: 1 },
        ],
      },
    } as never)
    const { result, wrapper } = await mountComposable(() => useElementTree())
    await flushPromises()

    const parent = result.pageTree.value[0]
    const child = parent.children[0]
    // isDescendantOf(source, target)：父 → 子成环 → 拒绝
    expect(result.allowDrop({ data: parent }, { data: child }, 'inner')).toBe(false)
    // 子 → 父不成环 → 允许（对照方向）
    expect(result.allowDrop({ data: child }, { data: parent }, 'inner')).toBe(true)
    expect(elApi.apiBatchMovePages).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('onMounted：自动 loadPages，apiGetPages 恰好调用一次', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({ data: { status: true, pages: [] } } as never)
    const { result, wrapper } = await mountComposable(() => useElementTree())
    await flushPromises()

    expect(elApi.apiGetPages).toHaveBeenCalledTimes(1)
    expect(result.loading.value).toBe(false)
    wrapper.unmount()
  })
})
