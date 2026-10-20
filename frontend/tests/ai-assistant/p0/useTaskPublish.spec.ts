/**
 * [P0] 必测 — 任务发布表单：智能体必选、YAML 解析标题、提交五项
 */
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as taskApi from '@/modules/ai-assistant/api/tasks'
import * as agentApi from '@/modules/ai-assistant/api/agents'
import { useTaskPublish } from '@/modules/ai-assistant/composables/useTaskPublish'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('@/modules/ai-assistant/api/tasks', () => ({
  listDevices: vi.fn(),
  submitTask: vi.fn(),
}))

vi.mock('@/modules/ai-assistant/api/agents', () => ({
  listAgents: vi.fn(),
}))

const YAML_TEXT = `
- title: 甲
  steps:
    - action: a
      assert: b
- title: 乙
  steps:
    - action: c
      assert: d
`

function yamlFile(text = YAML_TEXT, name = 'case.yaml'): File {
  return new File([text], name, { type: 'text/yaml' })
}

describe('[P0] useTaskPublish', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.listDevices).mockResolvedValue({
      status: true,
      data: {
        devices: [
          { serial: 'S1', model: 'M1', status: 'ONLINE', connection_type: 'USB', last_seen: '' },
        ],
      },
    })
    vi.mocked(agentApi.listAgents).mockResolvedValue({
      status: true,
      data: {
        agents: [
          {
            id: 10,
            name: '自动化小助手',
            status: 'active',
            route_configs: { device_control: { name: 'Agent-01号' } },
          },
        ],
      },
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('智能体必选：未选时不可提交', async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = '标题'
    result.form.value.device_serial = 'S1'
    await result.onConfigChange(yamlFile())
    expect(result.canSubmit()).toBe(false)

    result.form.value.agent_id = 10
    expect(result.canSubmit()).toBe(true)

    wrapper.unmount()
  })

  it('选 YAML 后解析出用例标题，换文件清空已选用例', async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onConfigChange(yamlFile())
    expect(result.caseTitles.value).toEqual(['甲', '乙'])
    result.form.value.case_title = '乙'

    await result.onConfigChange(yamlFile('- title: 丙\n  steps:\n    - action: a\n      assert: b\n'))
    expect(result.caseTitles.value).toEqual(['丙'])
    expect(result.form.value.case_title).toBe('')

    wrapper.unmount()
  })

  it('YAML 无法解析时给出可读错误且不生成选项', async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onConfigChange(yamlFile('- steps: []\n'))
    expect(result.caseTitles.value).toEqual([])
    expect(result.caseError.value).toContain('title')

    wrapper.unmount()
  })

  it('提交只带 title/agent_id/device_serial/case_title/config', async () => {
    vi.mocked(taskApi.submitTask).mockResolvedValue({
      status: true,
      data: { id: 1, status: 'pending' },
    })
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = '校准'
    result.form.value.agent_id = 10
    result.form.value.device_serial = 'S1'
    await result.onConfigChange(yamlFile())
    result.form.value.case_title = '乙'
    await result.submit()
    await flushPromises()

    expect(taskApi.submitTask).toHaveBeenCalledTimes(1)
    const fd = vi.mocked(taskApi.submitTask).mock.calls[0][0] as FormData
    expect(fd.get('title')).toBe('校准')
    expect(fd.get('agent_id')).toBe('10')
    expect(fd.get('device_serial')).toBe('S1')
    expect(fd.get('case_title')).toBe('乙')
    expect(fd.get('config')).toBeInstanceOf(File)
    expect(fd.get('goal')).toBeNull()
    expect(fd.get('documents')).toBeNull()

    wrapper.unmount()
  })

  it('打开弹窗立即刷新设备，关闭后不再轮询', async () => {
    vi.useFakeTimers()
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()
    const afterMount = vi.mocked(taskApi.listDevices).mock.calls.length

    result.openDialog()
    await flushPromises()
    expect(vi.mocked(taskApi.listDevices).mock.calls.length).toBe(afterMount + 1)

    vi.mocked(taskApi.listDevices).mockResolvedValue({
      status: true,
      data: {
        devices: [
          { serial: 'S1', model: 'M1', status: 'ONLINE', connection_type: 'USB', last_seen: '' },
          { serial: 'S2', model: 'M2', status: 'ONLINE', connection_type: 'USB', last_seen: '' },
        ],
      },
    })
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()
    expect(result.devices.value.some((d) => d.serial === 'S2')).toBe(true)

    const afterPoll = vi.mocked(taskApi.listDevices).mock.calls.length
    result.closeDialog()
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()
    expect(vi.mocked(taskApi.listDevices).mock.calls.length).toBe(afterPoll)

    wrapper.unmount()
  })
})
