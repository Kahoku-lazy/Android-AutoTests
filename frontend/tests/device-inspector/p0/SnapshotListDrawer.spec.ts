/**
 * [P0] 历史快照抽屉「一键清空」入口 — 二次确认与空态禁用
 * 目录：tests/device-inspector/p0/
 *
 * 口径来源：openspec/specs/device-inspector-page（快照删除需二次确认）。
 * 单测环境不注册 Element Plus 按需组件，故按本仓既有做法用替身：el-button 替身显式模拟
 * 「禁用时不派发 click」—— 未解析的原生元素在 jsdom 下对 disabled 仍会触发监听器，那样测不出来。
 */
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const { confirmMock } = vi.hoisted(() => ({ confirmMock: vi.fn() }))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: confirmMock },
}))
vi.mock('@/modules/device-inspector/api', () => ({
  apiCapture: vi.fn(),
  apiGetSnapshots: vi.fn(),
  apiGetLayers: vi.fn(),
  apiDeleteSnapshot: vi.fn(),
  apiClearSnapshots: vi.fn(),
  apiSaveToElements: vi.fn(),
  apiGetDevices: vi.fn(),
}))

import * as inspectorApi from '@/modules/device-inspector/api'
import { useElementStore } from '@/modules/device-inspector/store'
import SnapshotListDrawer from '@/modules/device-inspector/components/SnapshotListDrawer.vue'

/** el-button 替身：禁用时不派发 click（与 Element Plus 一致）。
 *  额外声明 type / text 两个 prop —— Element Plus 把它们消费成类名，替身读不到 DOM，
 *  故用 prop 断言「清空键不是 text 型」（text 型会被本页硬边皮肤正向排除）。 */
const ElButtonStub = {
  props: ['disabled', 'type', 'text'],
  emits: ['click'],
  template:
    '<button :disabled="disabled" @click="disabled ? null : $emit(\'click\')"><slot /></button>',
}

function ok(data) {
  return { data: { status: true, data } }
}

/** 挂载抽屉：同一个 pinia 实例交给测试与组件，确保两边拿到同一个 store */
function mountDrawer(snapshots) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useElementStore()
  store.snapshots = snapshots
  store.snapshotTotal = snapshots.length
  const wrapper = mount(SnapshotListDrawer, {
    global: {
      plugins: [pinia],
      stubs: {
        EmptyState: true,
        'el-drawer': { template: '<div><slot /></div>' },
        'el-button': ElButtonStub,
      },
    },
  })
  return { store, wrapper }
}

describe('[P0] SnapshotListDrawer 一键清空', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(inspectorApi.apiGetSnapshots).mockResolvedValue(ok({ items: [], total: 0 }) as never)
    vi.mocked(inspectorApi.apiClearSnapshots).mockResolvedValue(ok({ deleted: 2 }) as never)
  })

  it('「一键清空」不是 text 型按键；同一抽屉的行内删除键仍是 text 型图标键', () => {
    const { wrapper } = mountDrawer([{ id: 1 }])

    const buttons = wrapper.findAllComponents(ElButtonStub)
    expect(buttons).toHaveLength(2)
    const [clear, rowDelete] = buttons
    expect(clear.props('type')).toBe('danger')
    expect(clear.props('text')).toBeUndefined()
    expect(rowDelete.props('text')).toBe('')
  })

  it('没有快照时「一键清空」禁用，点击不弹确认也不发请求', async () => {
    const { wrapper } = mountDrawer([])

    const button = wrapper.find('[data-testid="snapshot-clear"]')
    expect(button.exists()).toBe(true)
    expect(button.attributes('disabled')).toBeDefined()

    await button.trigger('click')
    await flushPromises()

    expect(confirmMock).not.toHaveBeenCalled()
    expect(inspectorApi.apiClearSnapshots).not.toHaveBeenCalled()
  })

  it('确认后只调一次清空端点，确认文案写明不可恢复', async () => {
    confirmMock.mockResolvedValueOnce(undefined)
    const { wrapper } = mountDrawer([{ id: 1 }, { id: 2 }])

    await wrapper.find('[data-testid="snapshot-clear"]').trigger('click')
    await flushPromises()

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(String(confirmMock.mock.calls[0][0])).toContain('不可恢复')
    expect(inspectorApi.apiClearSnapshots).toHaveBeenCalledTimes(1)
  })

  it('取消确认不发起清空', async () => {
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    const { wrapper } = mountDrawer([{ id: 1 }])

    await wrapper.find('[data-testid="snapshot-clear"]').trigger('click')
    await flushPromises()

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(inspectorApi.apiClearSnapshots).not.toHaveBeenCalled()
  })
})
