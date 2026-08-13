/**
 * [P1] 建议测 — 元素定位页面树 composable（同级重名拒绝 / 层级限制 / confirm 取消 / bus 对称）
 * 目录：tests/element-locator/p1/
 *
 * siblingLabelTaken / getPageDepth 未导出：经 doRename / canCreateSubFolder 测可观察行为；
 * ElMessageBox.confirm 取消用 mockRejectedValueOnce 模拟，断言不调 apiDeletePage；
 * bus 对称用 mock event-bus：on 与 off 收到同一 handler 引用。
 * 统一 mock element-plus、模块 api、event-bus，不断真网络；wrapper 统一 afterEach unmount。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as elApi from '@/modules/element-locator/api'
import { bus } from '@/shared/event-bus'
import { useElementTree } from '@/modules/element-locator/composables/useElementTree'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))
vi.mock('@/modules/element-locator/api', () => ({
  apiGetPages: vi.fn(),
  apiCreatePage: vi.fn(),
  apiUpdatePage: vi.fn(),
  apiDeletePage: vi.fn(),
  apiGetPageElements: vi.fn(),
  apiBatchMovePages: vi.fn(),
  apiClearAll: vi.fn(),
}))
vi.mock('@/shared/event-bus', () => ({ bus: { on: vi.fn(), off: vi.fn(), emit: vi.fn() } }))

const busOn = vi.mocked(bus.on)
const busOff = vi.mocked(bus.off)

describe('[P1] element-locator useElementTree', () => {
  const mounted: VueWrapper[] = []

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    mounted.forEach((w) => w.unmount())
    mounted.length = 0
  })

  async function mountTree() {
    const { result, wrapper } = await mountComposable(() => useElementTree())
    mounted.push(wrapper)
    await flushPromises()
    return result
  }

  it('doRename：同级重名拒绝，不调 apiUpdatePage', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({
      data: {
        status: true,
        pages: [
          { id: 1, label: '页面A', is_folder: false, parent_id: null },
          { id: 2, label: '页面B', is_folder: false, parent_id: null },
        ],
      },
    } as never)
    const result = await mountTree()

    result.startEditLabel(result.pages.value[1])
    result.renameLabel.value = '页面A'
    await result.doRename()

    expect(vi.mocked(ElMessage.warning)).toHaveBeenCalledWith('同级名称「页面A」已存在，请使用其他名称')
    expect(elApi.apiUpdatePage).not.toHaveBeenCalled()
  })

  it('maxDepth：层级限制下 canCreateSubFolder 为 false', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({
      data: {
        status: true,
        pages: [
          { id: 1, label: 'L1', is_folder: true, parent_id: null },
          { id: 2, label: 'L2', is_folder: true, parent_id: 1 },
          { id: 3, label: 'L3', is_folder: true, parent_id: 2 },
          { id: 4, label: 'L4', is_folder: true, parent_id: 3 },
          { id: 5, label: 'L5', is_folder: true, parent_id: 4 },
          { id: 6, label: 'L6', is_folder: true, parent_id: 5 },
        ],
      },
    } as never)
    const result = await mountTree()

    expect(result.maxDepth.value).toBe(5)
    expect(result.canCreateSubFolder(null)).toBe(true) // 根层级不限制
    expect(result.canCreateSubFolder(5)).toBe(true) // 深度 4 < 5 → 边界内允许
    expect(result.canCreateSubFolder(6)).toBe(false) // 深度 5 ≥ 5 → 边界外拒绝
  })

  it('deletePage：confirm 取消（reject）不调 apiDeletePage', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({
      data: { status: true, pages: [{ id: 1, label: '页面A', is_folder: false, parent_id: null }] },
    } as never)
    vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce(new Error('cancel'))
    const result = await mountTree()

    await result.deletePage({ id: 1, label: '页面A', is_folder: false })

    expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1)
    expect(elApi.apiDeletePage).not.toHaveBeenCalled()
  })

  it('bus on/off 对称：unmount 后 off 收到与 on 相同的 handler', async () => {
    vi.mocked(elApi.apiGetPages).mockResolvedValue({ data: { status: true, pages: [] } } as never)
    const { wrapper } = await mountComposable(() => useElementTree())
    await flushPromises()

    expect(busOn).toHaveBeenCalledTimes(1)
    expect(busOn).toHaveBeenCalledWith('elements-saved', expect.any(Function))

    wrapper.unmount()

    expect(busOff).toHaveBeenCalledTimes(1)
    expect(busOff.mock.calls[0][0]).toBe('elements-saved')
    expect(busOff.mock.calls[0][1]).toBe(busOn.mock.calls[0][1])
  })
})
