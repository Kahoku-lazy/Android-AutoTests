/**
 * [P0] 必测 — 装配台「日志关键词」来源入口（spec: device-log-keyword-catalog）
 *
 * 目录：tests/ai-assistant/p0/
 * 断言：① 来源行出现在左侧工具来源列表（名称与说明性副标题）；
 * ② 选中后右侧渲染关键词目录面板；③ 该来源没有「交给助手」开关，也不进「未装配」提示。
 */
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

vi.mock('@/modules/ai-assistant/composables/useToolbox', () => ({
  useToolbox: () => ({
    items: ref([]),
    loading: ref(false),
    removeItem: vi.fn(),
    onSkillFolderPicked: vi.fn(),
    toggleItem: vi.fn(),
  }),
}))

vi.mock('@/modules/ai-assistant/composables/usePlatformTools', () => ({
  usePlatformTools: () => ({
    categories: ref([]),
    loading: ref(false),
    toggling: ref(false),
    expanded: ref([]),
    enabledCount: () => 0,
    allEnabled: () => false,
    toggleTool: vi.fn(),
    toggleCategory: vi.fn(),
  }),
}))

vi.mock('@/modules/ai-assistant/composables/usePlatformConfig', () => ({
  usePlatformConfig: () => ({
    // 两个总闸都关着：用来证明「日志关键词」不会被算作未装配来源
    config: ref({ enable_business_tools: false, enable_skills: false }),
    toggleFlag: vi.fn(),
  }),
}))

const fetchKeywords = vi.fn()
vi.mock('@/modules/ai-assistant/api/toolbox', () => ({
  fetchLogKeywords: (...args: unknown[]) => fetchKeywords(...args),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

import ToolboxPanel from '@/modules/ai-assistant/components/ToolboxPanel.vue'

const CATALOG = {
  keywords: [
    { keyword: 'switch_on', features: [{ id: 0, module: '设备开关', feature: '打开设备成功' }] },
  ],
  keyword_count: 1,
  feature_count: 1,
  origin: 'runtime',
  keyword_file: 'config/device_log_keywords.json',
  updated_at: '2026-09-28 18:20:11',
  note: '',
}

const stubs = {
  EmptyState: { props: ['text'], template: '<div class="stub-empty">{{ text }}</div>' },
  ErrorState: { template: '<div class="stub-error" />' },
  SkeletonCard: { template: '<div class="stub-skeleton" />' },
  AppTable: {
    props: ['columns', 'dataSource'],
    template: '<div class="stub-table" data-testid="log-keyword-table" />',
  },
  'el-collapse': { template: '<div><slot /></div>' },
  'el-collapse-item': { template: '<div><slot /></div>' },
  'el-switch': { template: '<span class="stub-switch" />' },
  'el-drawer': { template: '<div><slot /></div>' },
  'el-select': { template: '<div><slot /></div>' },
  'el-option': { template: '<div />' },
}

describe('[P0] 装配台日志关键词来源', () => {
  it('来源行在列表中，副标题是说明性文案且无总闸开关', async () => {
    fetchKeywords.mockResolvedValue({ status: true, data: CATALOG })
    const w = mount(ToolboxPanel, { global: { stubs } })
    const rows = w.findAll('.tb-source')
    const row = rows.find((item) => item.text().includes('日志关键词'))
    expect(row).toBeTruthy()
    expect(row?.text()).toContain('关键词 → 功能模块 / 功能点')
    expect(row?.find('.tb-source-gate').exists()).toBe(false)
    // 总闸都关着时，「未装配」提示只列平台业务与自定义 Skill
    const unarmed = w.find('.tb-unarmed')
    expect(unarmed.exists() ? unarmed.text() : '').not.toContain('日志关键词')
  })

  it('选中后右侧渲染关键词表格面板', async () => {
    fetchKeywords.mockResolvedValue({ status: true, data: CATALOG })
    const w = mount(ToolboxPanel, { global: { stubs } })
    const row = w.findAll('.tb-source').find((item) => item.text().includes('日志关键词'))
    await row?.trigger('click')
    await nextTick()
    await nextTick()
    expect(w.find('[data-testid="log-keyword-panel"]').exists()).toBe(true)
    expect(w.find('[data-testid="log-keyword-table"]').exists()).toBe(true)
    expect(w.find('[data-testid="log-keyword-count"]').text()).toContain('1 个关键词')
    expect(fetchKeywords).toHaveBeenCalled()
  })
})
