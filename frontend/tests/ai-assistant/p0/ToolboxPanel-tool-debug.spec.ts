/**
 * [P0] 装配台平台工具卡：停用/启用均有调试入口
 */
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'
import ToolboxPanel from '@/modules/ai-assistant/components/ToolboxPanel.vue'

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
    categories: ref([
      {
        key: '设备管理',
        icon: '📱',
        color: '#6BCB77',
        tools: [
          {
            name: 'list_apps',
            summary: '已装应用',
            icon: '📱',
            read_only: true,
            enabled: false,
          },
          {
            name: 'list_devices',
            summary: '全部设备',
            icon: '📱',
            read_only: true,
            enabled: true,
          },
        ],
      },
    ]),
    loading: ref(false),
    toggling: ref(false),
    expanded: ref(['设备管理']),
    enabledCount: (cat: { tools: { enabled: boolean }[] }) =>
      cat.tools.filter((t) => t.enabled).length,
    allEnabled: () => false,
    toggleTool: vi.fn(),
    toggleCategory: vi.fn(),
  }),
}))

vi.mock('@/modules/ai-assistant/composables/usePlatformConfig', () => ({
  usePlatformConfig: () => ({
    config: ref({
      enable_workspace_tools: false,
      enable_business_tools: true,
      enable_mcp_tools: false,
      enable_skills: false,
      enable_knowledge_base: false,
      skills_config: {},
      knowledge_sources: {},
    }),
    toggleFlag: vi.fn(),
  }),
}))

const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

describe('ToolboxPanel 平台工具调试入口', () => {
  it('停用工具卡仍显示调试并可跳转', async () => {
    const w = mount(ToolboxPanel, {
      props: { canManage: false },
      global: {
        stubs: {
          EmptyState: true,
          'el-collapse': { template: '<div><slot /></div>' },
          'el-collapse-item': { template: '<div><slot name="title" /><slot /></div>' },
          'el-switch': true,
        },
      },
    })
    const debugBtns = w.findAll('.pt-debug-btn')
    expect(debugBtns.length).toBe(2)
    await debugBtns[0].trigger('click')
    expect(push).toHaveBeenCalledWith('/ai-assistant/toolbox/tools/list_apps')
  })
})
