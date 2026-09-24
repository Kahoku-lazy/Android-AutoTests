/**
 * [P0] 设备提示词区：三份提示词各自独立编辑 / 取消、历史入口唯一
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

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

import DevicePromptPanel from '@/modules/ai-assistant/components/DevicePromptPanel.vue'

const SAVED = {
  status: true,
  data: { planner: 'p0', executor: 'e0', verifier: 'v0' },
}

function mountPanel(canManage = true) {
  return mount(DevicePromptPanel, {
    props: { canManage },
    global: {
      stubs: {
        'el-collapse': { template: '<div><slot /></div>' },
        'el-collapse-item': { template: '<div><slot name="title" /><slot /></div>' },
        'el-drawer': { template: '<div><slot /></div>' },
      },
    },
  })
}

function actionGroups(wrapper: ReturnType<typeof mountPanel>) {
  return wrapper.findAll('.tb-prompt-actions')
}

describe('DevicePromptPanel 按份独立编辑', () => {
  beforeEach(() => {
    fetchPrompts.mockReset().mockResolvedValue(SAVED)
    updatePrompts.mockReset()
    fetchArchives.mockReset().mockResolvedValue({ status: true, data: { items: [] } })
  })

  it('点某一份的编辑只有该份变成输入框', async () => {
    const w = mountPanel()
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))
    expect(w.findAll('.tb-prompt-textarea')).toHaveLength(0)
    expect(actionGroups(w).map((g) => g.findAll('button').map((b) => b.text()))).toEqual([
      ['编辑'],
      ['编辑'],
      ['编辑'],
    ])

    await actionGroups(w)[0].findAll('button')[0].trigger('click')

    expect(w.findAll('.tb-prompt-edit')).toHaveLength(1)
    const textareas = w.findAll('.tb-prompt-textarea')
    expect(textareas).toHaveLength(1)
    expect((textareas[0].element as HTMLTextAreaElement).value).toBe('p0')
    expect(actionGroups(w)[0].findAll('button').map((b) => b.text())).toEqual(['取消', '保存'])
    expect(actionGroups(w)[1].findAll('button').map((b) => b.text())).toEqual(['编辑'])
    expect(actionGroups(w)[2].findAll('button').map((b) => b.text())).toEqual(['编辑'])
  })

  it('可同时编辑多份，各自的输入框互不覆盖', async () => {
    const w = mountPanel()
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))

    await actionGroups(w)[0].findAll('button')[0].trigger('click')
    await actionGroups(w)[1].findAll('button')[0].trigger('click')

    const textareas = w.findAll('.tb-prompt-textarea')
    expect(textareas).toHaveLength(2)
    expect(textareas.map((t) => (t.element as HTMLTextAreaElement).value)).toEqual(['p0', 'e0'])

    await textareas[0].setValue('p1')
    expect((w.findAll('.tb-prompt-textarea')[1].element as HTMLTextAreaElement).value).toBe('e0')
  })

  it('取消一份只写该份，另一份草稿保持不动', async () => {
    updatePrompts.mockResolvedValueOnce({
      status: true,
      data: { planner: 'p0', executor: 'e1', verifier: 'v0' },
    })

    const w = mountPanel()
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))

    await actionGroups(w)[0].findAll('button')[0].trigger('click')
    await actionGroups(w)[1].findAll('button')[0].trigger('click')
    await w.findAll('.tb-prompt-textarea')[0].setValue('p1')
    await w.findAll('.tb-prompt-textarea')[1].setValue('e1')

    // 点「执行」的取消（该组第二个按钮）
    await actionGroups(w)[1].findAll('button')[0].trigger('click')
    await vi.waitFor(() => expect(updatePrompts).toHaveBeenCalledTimes(1))

    expect(updatePrompts).toHaveBeenCalledWith(
      { planner: 'p0', executor: 'e1', verifier: 'v0' },
      'auto',
    )
    expect(actionGroups(w)[1].findAll('button').map((b) => b.text())).toEqual(['编辑'])
    expect(actionGroups(w)[0].findAll('button').map((b) => b.text())).toEqual(['取消', '保存'])
    expect((w.findAll('.tb-prompt-textarea')[0].element as HTMLTextAreaElement).value).toBe('p1')
  })

  it('离开来源（组件卸载）时有改动的份自动落库', async () => {
    updatePrompts.mockResolvedValueOnce({
      status: true,
      data: { planner: 'p1', executor: 'e0', verifier: 'v0' },
    })

    const w = mountPanel()
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))

    await actionGroups(w)[0].findAll('button')[0].trigger('click')
    await w.findAll('.tb-prompt-textarea')[0].setValue('p1')
    w.unmount()

    await vi.waitFor(() => expect(updatePrompts).toHaveBeenCalledTimes(1))
    expect(updatePrompts).toHaveBeenCalledWith(
      { planner: 'p1', executor: 'e0', verifier: 'v0' },
      'auto',
    )
  })

  it('历史记录入口只在页头出现一次', async () => {
    const w = mountPanel()
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))

    expect(w.findAll('.tb-cat-actions button').map((b) => b.text())).toEqual(['查看历史记录'])
  })

  it('非管理员没有编辑与历史入口', async () => {
    const w = mountPanel(false)
    await vi.waitFor(() => expect(w.findAll('.tb-prompt-md')).toHaveLength(3))

    expect(w.findAll('.tb-prompt-actions')).toHaveLength(0)
    expect(w.findAll('.tb-cat-actions')).toHaveLength(0)
    expect(w.findAll('.tb-prompt-textarea')).toHaveLength(0)
  })
})
