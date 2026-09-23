/**
 * [P0] 元素表分页行数 — 每页 14 行（回归：行数偏少时表格下方留出大片空白）
 * 目录：tests/device-inspector/p0/
 *
 * 口径来源：openspec/specs/device-inspector-page（元素表格常驻与固定 14 行分页）。
 * 单测环境不为 el-* 注册按需组件（vite.config.js 的 isTest 分支），故按本仓既有做法 stub 掉
 * 表格与 el-*，断言面板自身的分页接线：首屏行数 = 14、总页数 = ceil(N / 14)。
 */
import { createPinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StructureAnalysisPanel from '@/modules/device-inspector/components/StructureAnalysisPanel.vue'
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from '@/modules/device-inspector/constants'

/** 表格替身：把面板下发的行数渲染成 DOM 行，便于断言「首屏渲染了几行」 */
const AppTableStub = {
  name: 'AppTable',
  props: ['dataSource'],
  template: '<div class="stub-table"><div v-for="(row, i) in dataSource" :key="i" class="stub-row" /></div>',
}

function panelElement(seq: number) {
  return {
    seq,
    _idx: seq,
    _rowKey: `s${seq}`,
    level1: 'content_widget',
    level2: 'text',
    text: `元素 ${seq}`,
    coords: { x: 0, y: seq, w: 1, h: 1, cx: 0, cy: 0, bounds: '[0,0][1,1]' },
    primary: { xpath: '', stable: false },
  }
}

function mountPanel(count: number) {
  const elements = Array.from({ length: count }, (_, i) => panelElement(i + 1))
  return mount(StructureAnalysisPanel, {
    props: { groups: [], activeGroupId: 'content_widget/text', elements, selected: null },
    global: {
      plugins: [createPinia()],
      stubs: {
        AppTable: AppTableStub,
        EmptyState: true,
        'el-button': { template: '<button><slot /></button>' },
        'el-checkbox': true,
        'el-tag': { template: '<span><slot /></span>' },
        'el-dialog': { template: '<div><slot /></div>' },
      },
    },
  })
}

describe('[P0] StructureAnalysisPanel 分页行数', () => {
  it('行数常量唯一登记：默认值与选项集一致', () => {
    expect(DEFAULT_PAGE_SIZE).toBe(14)
    expect(PAGE_SIZE_OPTIONS).toEqual([14])
  })

  it('40 条元素首屏渲染 14 行，分页为 3 页', () => {
    const wrapper = mountPanel(40)
    expect(wrapper.findAll('.stub-row')).toHaveLength(14)
    const info = wrapper.find('.sap-page-info').text()
    expect(info).toContain('第 1 / 3 页')
    expect(info).toContain('共 40 条')
  })

  it('第 2 页仍是满页 14 行', async () => {
    const wrapper = mountPanel(40)
    await wrapper.find('[data-testid="page-next"]').trigger('click')
    expect(wrapper.find('.sap-page-info').text()).toContain('第 2 / 3 页')
    expect(wrapper.findAll('.stub-row')).toHaveLength(14)
  })

  it('末页只渲染剩余 12 行', async () => {
    const wrapper = mountPanel(40)
    await wrapper.find('[data-testid="page-next"]').trigger('click')
    await wrapper.find('[data-testid="page-next"]').trigger('click')
    expect(wrapper.find('.sap-page-info').text()).toContain('第 3 / 3 页')
    expect(wrapper.findAll('.stub-row')).toHaveLength(12)
  })
})
