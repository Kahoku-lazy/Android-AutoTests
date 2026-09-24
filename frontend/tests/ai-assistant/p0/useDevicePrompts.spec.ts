/**
 * [P0] 设备提示词：按角色独立编辑 / 独立保存、退出编辑自动保存、历史覆盖与永久档删除
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

// 组件外调用 onMounted 不会执行，这里直接执行，便于断言首屏加载
vi.mock('vue', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue')>()
  return { ...actual, onMounted: (fn: () => void) => fn() }
})

const fetchPrompts = vi.fn()
const updatePrompts = vi.fn()
const fetchArchives = vi.fn()
const fetchArchive = vi.fn()
const removeArchive = vi.fn()
const restoreArchive = vi.fn()

vi.mock('@/modules/ai-assistant/api/toolbox', () => ({
  fetchDevicePrompts: (...args: unknown[]) => fetchPrompts(...args),
  updateDevicePrompts: (...args: unknown[]) => updatePrompts(...args),
  fetchDevicePromptArchives: (...args: unknown[]) => fetchArchives(...args),
  fetchDevicePromptArchive: (...args: unknown[]) => fetchArchive(...args),
  deleteDevicePromptArchive: (...args: unknown[]) => removeArchive(...args),
  restoreDevicePromptArchive: (...args: unknown[]) => restoreArchive(...args),
}))

import { ElMessageBox } from 'element-plus'
import { PROMPT_OVERWRITE_CONFIRM } from '@/modules/ai-assistant/constants'
import { useDevicePrompts } from '@/modules/ai-assistant/composables/useDevicePrompts'
import DevicePromptHistoryDrawer from '@/modules/ai-assistant/components/DevicePromptHistoryDrawer.vue'

const SAVED = {
  status: true,
  data: { planner: 'p0', executor: 'e0', verifier: 'v0', agent_id: 10 },
}

function mountHistory(archives: unknown[]) {
  return mount(DevicePromptHistoryDrawer, {
    props: { modelValue: true, archives: archives as never },
    global: { stubs: { 'el-drawer': { template: '<div><slot /></div>' } } },
  })
}

describe('useDevicePrompts 保存与退出编辑', () => {
  beforeEach(() => {
    fetchPrompts.mockReset().mockResolvedValue(SAVED)
    updatePrompts.mockReset()
    fetchArchives.mockReset().mockResolvedValue({ status: true, data: { items: [] } })
    fetchArchive.mockReset()
    removeArchive.mockReset()
    restoreArchive.mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
  })

  it('保存前用固定文案二次确认', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
    updatePrompts.mockResolvedValueOnce(SAVED)

    const { save, draft, startEdit } = useDevicePrompts()
    await vi.waitFor(() => expect(draft.value.planner).toBe('p0'))
    startEdit('planner')
    await save('planner')

    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      PROMPT_OVERWRITE_CONFIRM,
      '确认保存',
      expect.anything(),
    )
  })

  it('取消确认时不写库', async () => {
    vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce('cancel')

    const { save, draft, startEdit } = useDevicePrompts()
    await vi.waitFor(() => expect(draft.value.planner).toBe('p0'))
    startEdit('planner')
    draft.value.planner = 'p1'

    expect(await save('planner')).toBe(false)
    expect(updatePrompts).not.toHaveBeenCalled()
  })

  it('确认后以 permanent 提交', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
    updatePrompts.mockResolvedValueOnce(SAVED)

    const { save, draft, startEdit } = useDevicePrompts()
    await vi.waitFor(() => expect(draft.value.planner).toBe('p0'))
    startEdit('planner')
    await save('planner')

    expect(updatePrompts).toHaveBeenCalledWith(
      expect.objectContaining({ planner: 'p0' }),
      'permanent',
    )
  })

  it('保存一份时另两份取已保存值，不带入另一份未保存的草稿', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
    updatePrompts.mockResolvedValueOnce({
      status: true,
      data: { planner: 'p1', executor: 'e0', verifier: 'v0' },
    })

    const { save, draft, prompts, startEdit, isEditing } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))

    startEdit('planner')
    startEdit('executor')
    draft.value.planner = 'p1'
    draft.value.executor = 'e1'

    expect(await save('planner')).toBe(true)
    expect(updatePrompts).toHaveBeenCalledWith(
      { planner: 'p1', executor: 'e0', verifier: 'v0' },
      'permanent',
    )
    // 执行既没被写库、也没被退出编辑态或清掉草稿
    expect(prompts.value.executor).toBe('e0')
    expect(draft.value.executor).toBe('e1')
    expect(isEditing('executor')).toBe(true)
    expect(isEditing('planner')).toBe(false)
  })

  it('进入一份编辑不影响另一份的编辑态与草稿', async () => {
    const { draft, prompts, startEdit, isEditing } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))

    startEdit('planner')
    draft.value.planner = 'p1'
    startEdit('executor')

    expect(isEditing('planner')).toBe(true)
    expect(isEditing('executor')).toBe(true)
    expect(draft.value.planner).toBe('p1')
    expect(draft.value.executor).toBe('e0')
  })

  it('无改动退出编辑不发请求', async () => {
    const { autoSaveIfDirty, prompts } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))

    expect(await autoSaveIfDirty()).toBe(false)
    expect(updatePrompts).not.toHaveBeenCalled()
  })

  it('有改动退出编辑按 auto 自动保存', async () => {
    const { draft, autoSaveIfDirty, prompts, startEdit } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))
    startEdit('planner')
    draft.value.planner = 'p1'
    updatePrompts.mockResolvedValueOnce({
      status: true,
      data: { planner: 'p1', executor: 'e0', verifier: 'v0' },
    })

    expect(await autoSaveIfDirty()).toBe(true)
    expect(updatePrompts).toHaveBeenCalledWith(expect.objectContaining({ planner: 'p1' }), 'auto')
    expect(prompts.value.planner).toBe('p1')
  })

  it('取消一份只处理该份：另一份仍在编辑态且草稿不被写库', async () => {
    const { draft, prompts, startEdit, cancelEdit, isEditing } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))

    startEdit('planner')
    startEdit('executor')
    draft.value.planner = 'p1'
    draft.value.executor = 'e1'
    updatePrompts.mockResolvedValueOnce({
      status: true,
      data: { planner: 'p0', executor: 'e1', verifier: 'v0' },
    })

    await cancelEdit('executor')

    expect(updatePrompts).toHaveBeenCalledTimes(1)
    expect(updatePrompts).toHaveBeenCalledWith(
      { planner: 'p0', executor: 'e1', verifier: 'v0' },
      'auto',
    )
    expect(isEditing('executor')).toBe(false)
    expect(isEditing('planner')).toBe(true)
    expect(draft.value.planner).toBe('p1')
  })

  it('取消未改动的一份不写库', async () => {
    const { prompts, startEdit, cancelEdit, isEditing } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))

    startEdit('verifier')
    await cancelEdit('verifier')

    expect(updatePrompts).not.toHaveBeenCalled()
    expect(isEditing('verifier')).toBe(false)
  })

  it('覆盖历史档后当前提示词被替换且退出全部编辑态', async () => {
    const { prompts, startEdit, isEditing, restoreArchive: doRestore } = useDevicePrompts()
    await vi.waitFor(() => expect(prompts.value.planner).toBe('p0'))
    startEdit('planner')
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
    restoreArchive.mockResolvedValueOnce({
      status: true,
      data: { planner: 'old', executor: 'e', verifier: 'v' },
    })

    expect(await doRestore(7)).toBe(true)
    expect(restoreArchive).toHaveBeenCalledWith(7)
    expect(prompts.value.planner).toBe('old')
    expect(isEditing('planner')).toBe(false)
  })

  it('打开历史记录拉列表，删除永久档走 delete 接口', async () => {
    const { openHistory, removePermanentArchive, archives } = useDevicePrompts()
    fetchArchives.mockResolvedValueOnce({
      status: true,
      data: { items: [{ id: 9, kind: 'permanent' }] },
    })
    await openHistory()
    expect(archives.value.map((item) => item.id)).toEqual([9])

    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
    removeArchive.mockResolvedValueOnce({ status: true })
    fetchArchives.mockResolvedValueOnce({ status: true, data: { items: [] } })

    expect(await removePermanentArchive(9)).toBe(true)
    expect(removeArchive).toHaveBeenCalledWith(9)
  })
})

describe('DevicePromptHistoryDrawer', () => {
  it('自动档没有删除入口，永久档有', () => {
    const wrapper = mountHistory([
      {
        id: 1,
        kind: 'auto',
        created_at: '2026-09-23T10:00:00',
        planner_length: 10,
        executor_length: 10,
        verifier_length: 10,
      },
      {
        id: 2,
        kind: 'permanent',
        created_at: '2026-09-23T11:00:00',
        planner_length: 20,
        executor_length: 20,
        verifier_length: 20,
      },
    ])

    const items = wrapper.findAll('.dph-item')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('自动存档')
    expect(items[0].findAll('button').map((b) => b.text())).toEqual(['预览', '覆盖当前'])
    expect(items[1].findAll('button').map((b) => b.text())).toEqual(['预览', '覆盖当前', '删除'])
  })

  it('点覆盖与删除会带对应 id 抛事件', async () => {
    const wrapper = mountHistory([{ id: 5, kind: 'permanent', created_at: '2026-09-23T11:00:00' }])

    const buttons = wrapper.findAll('.dph-actions button')
    await buttons[1].trigger('click')
    await buttons[2].trigger('click')

    expect(wrapper.emitted('restore')).toEqual([[5]])
    expect(wrapper.emitted('remove')).toEqual([[5]])
  })
})
