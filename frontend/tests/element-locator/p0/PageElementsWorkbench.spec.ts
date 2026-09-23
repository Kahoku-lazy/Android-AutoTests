/**
 * [P0] 必测 — 页面元素工作台呈现与可编辑面（收敛口径）
 * 目录：tests/element-locator/p0/
 *
 * 口径来源：openspec/specs/element-locator-element-fields 与 element-locator-page-workbench。
 * 单测环境不为 el-* 注册按需组件（vite.config.js 的 isTest 分支），故按本仓既有做法 stub 掉
 * 表格与 el-*，断言列集合、缩略图占位、交互标注与「只有四列可编辑」。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PageElementsWorkbench from '@/modules/element-locator/components/PageElementsWorkbench.vue'

vi.mock('@/modules/element-locator/api', () => ({
  apiPageItems: vi.fn(),
  apiUpdateElement: vi.fn(),
  createPageElement: vi.fn(),
  batchDeleteElements: vi.fn(),
}))
import * as elApi from '@/modules/element-locator/api'

/** 表格替身：渲染列名与行，并把每格的具名插槽透传出来，便于断言单元格内容 */
const AppTableStub = {
  name: 'AppTable',
  props: ['columns', 'dataSource'],
  template: `
    <div class="stub-table">
      <div class="stub-head">
        <span v-for="col in columns" :key="col.key || col.dataIndex" class="stub-col">{{ col.label }}</span>
      </div>
      <div v-for="(row, i) in dataSource" :key="i" class="stub-row">
        <span v-for="col in columns" :key="col.key || col.dataIndex" class="stub-cell">
          <slot :name="'cell-' + (col.dataIndex || col.key)" :row="row" :value="row[col.dataIndex]">
            {{ row[col.dataIndex] }}
          </slot>
        </span>
      </div>
    </div>`,
}

function rawRow(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    alias: '登录按钮',
    seq: 3,
    text_val: '登录',
    primary_xpath: "//android.widget.Button[@text='登录']",
    primary_stable: true,
    thumbnail_path: 'locator/pages/1/el_x.png',
    is_test_point: false,
    clickable: true,
    long_clickable: false,
    scrollable: false,
    checkable: false,
    checked: false,
    enabled: true,
    focusable: true,
    ...overrides,
  }
}

async function mountWorkbench(rows: Record<string, unknown>[]) {
  vi.mocked(elApi.apiPageItems).mockResolvedValue(
    { data: { status: true, elements: rows, total: rows.length } } as never,
  )
  const wrapper = mount(PageElementsWorkbench, {
    props: { pageId: 1 },
    global: {
      stubs: {
        AppTable: AppTableStub,
        EmptyState: true,
        ErrorState: true,
        SkeletonCard: true,
        'el-button': { template: '<button><slot /></button>' },
        'el-checkbox': true,
        'el-switch': true,
        'el-dialog': { template: '<div><slot /></div>' },
        'el-form': { template: '<form><slot /></form>' },
        'el-form-item': { template: '<div><slot /></div>' },
        'el-input': { template: '<input />' },
      },
    },
  })
  await flushPromises()
  return wrapper
}

describe('[P0] 元素工作台呈现列集合', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('表头只有收敛后的七列，不含 resource-id 与坐标列', async () => {
    const wrapper = await mountWorkbench([rawRow()])
    const headers = wrapper.findAll('.stub-col').map((node) => node.text())
    expect(headers).toEqual([
      '',
      '缩略图',
      '元素名称',
      '序号',
      '文本',
      '主定位',
      '交互标注',
      '测试点',
    ])
    expect(headers).not.toContain('resource-id')
    expect(headers).not.toContain('坐标')
  })

  it('缩略图列渲染图片；无缩略图时空占位（不出现破图）', async () => {
    const wrapper = await mountWorkbench([
      rawRow(),
      rawRow({ id: 2, seq: 4, thumbnail_path: '' }),
    ])
    expect(wrapper.findAll('.page-elements-thumb')).toHaveLength(1)
    expect(wrapper.findAll('.page-elements-empty').length).toBeGreaterThan(0)
  })

  it('交互标注列只列真值为真的标志', async () => {
    const wrapper = await mountWorkbench([rawRow()])
    const flags = wrapper.findAll('.page-elements-flag').map((node) => node.text())
    expect(flags).toEqual(['可点击', '启用', '可聚焦'])
  })

  it('序号列展示元素序号', async () => {
    const wrapper = await mountWorkbench([rawRow()])
    expect(wrapper.find('.page-elements-seq').text()).toBe('3')
  })
})

describe('[P0] 元素工作台可编辑面', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('只有元素名称、文本、主定位可编辑，序号与交互标注为纯文本', async () => {
    const wrapper = await mountWorkbench([rawRow()])
    const editable = wrapper.findAll('.editable-cell').map((node) => node.text())
    expect(editable).toEqual(['登录按钮', '登录', "//android.widget.Button[@text='登录']"])
    expect(wrapper.find('.page-elements-seq').exists()).toBe(true)
  })
})
