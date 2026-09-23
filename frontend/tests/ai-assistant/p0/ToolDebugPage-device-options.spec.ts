/**
 * [P0] 工具调试页：带候选的参数渲染为下拉；候选为空给提示且仍可手输
 * （替代 tasks.md 2.3 的人工走查）
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'
import ToolDebugPage from '@/modules/ai-assistant/ToolDebugPage.vue'

const schema = ref<Record<string, unknown> | null>(null)
const form = ref<Record<string, unknown>>({})

vi.mock('@/modules/ai-assistant/composables/useToolDebug', () => ({
  useToolDebug: () => ({
    schema,
    form,
    loading: ref(false),
    invoking: ref(false),
    error: ref(''),
    invokeError: ref(''),
    result: ref(null),
    resultText: ref(''),
    screenshot: ref(null),
    canExecute: ref(true),
    loadSchema: vi.fn(),
    runInvoke: vi.fn(),
  }),
}))

vi.mock('@/shared/composables/useAuthUser', () => ({
  useAuthUser: () => ({ isSuperuser: ref(true) }),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { toolName: 'tap_screen' } }),
}))

function mountPage() {
  return mount(ToolDebugPage, {
    global: {
      stubs: {
        WorkbenchHeader: true,
        WorkbenchCrumbs: true,
        EmptyState: true,
        ErrorState: true,
        'el-select': { template: '<div class="stub-select"><slot /></div>' },
        'el-option': { template: '<div class="stub-option" />' },
      },
    },
  })
}

describe('ToolDebugPage 设备参数候选', () => {
  beforeEach(() => {
    schema.value = null
    form.value = {}
  })

  it('带候选的参数渲染为下拉并列出候选项，其余参数仍是输入框', () => {
    schema.value = {
      name: 'tap_screen',
      summary: '点击或长按',
      read_only: true,
      parameters: [
        {
          name: 'serial',
          type: 'str',
          required: true,
          options: [
            { value: 'RF8', label: '空闲机 (RF8)' },
            { value: 'AB1', label: '备用机 (AB1)' },
          ],
        },
        { name: 'mode', type: 'str', required: false, default: 'click' },
      ],
    }
    const w = mountPage()
    expect(w.findAll('.stub-select').length).toBe(1)
    expect(w.findAll('.stub-option').length).toBe(2)
    expect(w.findAll('.td-input').length).toBe(1)
    expect(w.find('.td-field-note').exists()).toBe(false)
  })

  it('候选为空时给出可读提示且不禁用执行', () => {
    schema.value = {
      name: 'tap_screen',
      summary: '点击或长按',
      read_only: true,
      parameters: [{ name: 'serial', type: 'str', required: true, options: [] }],
    }
    const w = mountPage()
    expect(w.find('.stub-select').exists()).toBe(true)
    expect(w.find('.td-field-note').text()).toContain('可手动填写')
    expect(w.find('.td-run').attributes('disabled')).toBeUndefined()
  })
})
