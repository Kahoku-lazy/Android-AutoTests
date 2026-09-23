/**
 * [P0] 元素表「缩略图」列 = 定位入口 — 单击即在手机画面上高亮对应矩形框
 * 目录：tests/device-inspector/p0/
 *
 * 口径来源：openspec/specs/device-inspector-page（手机画面按当前分组圈选并保留选中高亮）。
 * 既有面板用例的 AppTable 替身不渲染单元格插槽，测不到本变更；这里让替身把 cell-thumbnail 渲染出来。
 */
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { useElementStore } from '@/modules/device-inspector/store'
import StructureAnalysisPanel from '@/modules/device-inspector/components/StructureAnalysisPanel.vue'

/** AppTable 替身：每行只渲染缩略图格的真实内容（本用例只需该格） */
const AppTableStub = {
  props: ['dataSource'],
  template:
    '<div class="stub-table">' +
    '<div v-for="(row, i) in dataSource" :key="i" class="stub-row">' +
    '<slot name="cell-thumbnail" :row="row" />' +
    '</div></div>',
}

/** el-dialog 替身：仅在 modelValue 为真时渲染内容，便于断言「有没有打开预览」 */
const ElDialogStub = {
  props: ['modelValue'],
  template: '<div v-if="modelValue" class="stub-dialog"><slot /></div>',
}

function panelElement(seq, extra = {}) {
  return {
    seq,
    _idx: seq,
    _rowKey: 's' + seq,
    level1: 'content_widget',
    level2: 'icon',
    text: '',
    class_name: 'android.widget.ImageView',
    class_simple: 'ImageView',
    resource_id: '',
    content_desc: '',
    coords: { x: 0, y: seq * 10, w: 10, h: 10, cx: 5, cy: seq * 10 + 5, bounds: '[0,0][10,10]' },
    primary: { xpath: '', stable: false },
    thumbnail_path: '',
    flags: {},
    ...extra,
  }
}

function mountPanel(elements) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useElementStore()
  const wrapper = mount(StructureAnalysisPanel, {
    props: { groups: [], activeGroupId: 'content_widget/icon', elements, selected: null },
    global: {
      plugins: [pinia],
      stubs: {
        AppTable: AppTableStub,
        EmptyState: true,
        'el-dialog': ElDialogStub,
        'el-button': { template: '<button><slot /></button>' },
        'el-checkbox': true,
        'el-tag': { template: '<span><slot /></span>' },
      },
    },
  })
  return { store, wrapper }
}

describe('[P0] 缩略图列定位高亮', () => {
  it('单击缩略图列（无缩略图数据）即 emit select，且不进重命名、不动勾选', async () => {
    const elements = [panelElement(1), panelElement(2)]
    const { store, wrapper } = mountPanel(elements)

    const cells = wrapper.findAll('[data-testid="thumb-locate"]')
    expect(cells).toHaveLength(2)

    await cells[1].trigger('click')

    const emitted = wrapper.emitted('select') as unknown[][]
    expect(emitted).toHaveLength(1)
    // 表格经分页 composable 下发的是响应式代理，故按行键断言行对象而不是引用
    expect((emitted[0][0] as { _idx: number })._idx).toBe(elements[1]._idx)
    expect(wrapper.find('.sap-name-input').exists()).toBe(false)
    expect(store.checkedIds.size).toBe(0)
  })

  it('单击不打开放大预览，双击才打开（该行有缩略图数据时）', async () => {
    const elements = [panelElement(1, { thumbnail_path: 'inspector/thumbs/x/el_0.png' })]
    const { wrapper } = mountPanel(elements)

    await wrapper.find('[data-testid="thumb-locate"]').trigger('click')
    expect(wrapper.find('.stub-dialog').exists()).toBe(false)

    await wrapper.find('.sap-thumb-wrap').trigger('dblclick')
    expect(wrapper.find('.stub-dialog').exists()).toBe(true)
  })

  it('没有缩略图数据时双击不打开预览', async () => {
    const { wrapper } = mountPanel([panelElement(1)])

    await wrapper.find('[data-testid="thumb-locate"]').trigger('dblclick')

    expect(wrapper.find('.stub-dialog').exists()).toBe(false)
  })
})
