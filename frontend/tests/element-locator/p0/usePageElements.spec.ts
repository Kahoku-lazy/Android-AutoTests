/**
 * [P0] 必测 — 元素行工作台的勾选语义（与 openspec/specs/element-locator-page-workbench 对齐）
 * 目录：tests/element-locator/p0/
 *
 * 口径：单格更新失败后的重载 MUST NOT 清空用户勾选；批量删除成功后 MUST 清空。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { usePageElements } from '@/modules/element-locator/composables/usePageElements'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))
vi.mock('@/modules/element-locator/api', () => ({
  apiPageItems: vi.fn(),
  apiUpdateElement: vi.fn(),
  createPageElement: vi.fn(),
  batchDeleteElements: vi.fn(),
}))
import { ElMessage } from 'element-plus'
import * as elApi from '@/modules/element-locator/api'

/** 与 views_page_elements._element_payload 同形的 wire 行 */
function rawRow(id: number) {
  return {
    id,
    page_id: 1,
    alias: `元素${id}`,
    text_val: '',
    resource_id: `com.demo:id/${id}`,
    bounds: '[0,0][1,1]',
    seq: id,
    primary_xpath: '//a',
    primary_stable: true,
    thumbnail_path: '',
    clickable: false,
    long_clickable: false,
    scrollable: false,
    checkable: false,
    checked: false,
    enabled: true,
    focusable: false,
    is_test_point: false,
    notes: '',
    created_at: '2026-09-23 00:00:00',
  }
}

const Host = defineComponent({
  setup() {
    return { api: usePageElements(() => 1) }
  },
  template: '<div />',
})

type WorkbenchApi = ReturnType<typeof usePageElements>

async function mountWorkbench() {
  vi.mocked(elApi.apiPageItems).mockResolvedValue({
    data: { status: true, elements: [rawRow(1), rawRow(2)], total: 2 },
  } as never)
  const wrapper = mount(Host)
  await flushPromises()
  return (wrapper.vm as unknown as { api: WorkbenchApi }).api
}

describe('[P0] 元素行勾选语义', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('单格更新失败后重载，仍保留已勾选的行', async () => {
    const api = await mountWorkbench()
    api.toggleRow(1)
    api.toggleRow(2)
    vi.mocked(elApi.apiUpdateElement).mockResolvedValue({
      data: { status: false, message: '元素名称不能为空' },
    } as never)

    const ok = await api.updateField(api.rows.value[0], 'alias', '')

    expect(ok).toBe(false)
    expect(ElMessage.error).toHaveBeenCalledWith('元素名称不能为空')
    expect(api.selectedIds.value).toEqual([1, 2])
  })

  it('批量删除成功后清空勾选（默认重载语义不变）', async () => {
    const api = await mountWorkbench()
    api.toggleRow(1)
    vi.mocked(elApi.batchDeleteElements).mockResolvedValue({
      data: { status: true, data: { deleted: 1, pages: 0, elements: 1 } },
    } as never)

    const ok = await api.removeSelected()

    expect(ok).toBe(true)
    expect(api.selectedIds.value).toEqual([])
  })

  it('切换页面重载时清空勾选（默认语义）', async () => {
    const api = await mountWorkbench()
    api.toggleRow(1)

    await api.load()

    expect(api.selectedIds.value).toEqual([])
  })
})
