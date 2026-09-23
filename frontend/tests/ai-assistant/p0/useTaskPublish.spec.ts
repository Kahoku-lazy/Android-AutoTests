/**
 * [P0] 必测 — 任务发布表单：标题必填、附件 accept
 */
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as taskApi from '@/modules/ai-assistant/api/tasks'
import { useTaskPublish } from '@/modules/ai-assistant/composables/useTaskPublish'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('@/modules/ai-assistant/api/tasks', () => ({
  listDevices: vi.fn(),
  submitTask: vi.fn(),
}))

describe('[P0] useTaskPublish', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.listDevices).mockResolvedValue({
      status: true,
      data: { devices: [{ serial: 'S1', model: 'M1', status: 'ONLINE', connection_type: 'USB', last_seen: '' }] },
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('canSubmit 要求标题与目标均非空', async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    expect(result.canSubmit()).toBe(false)
    result.form.value.goal = '做点事'
    expect(result.canSubmit()).toBe(false)
    result.form.value.title = '标题'
    expect(result.canSubmit()).toBe(true)

    wrapper.unmount()
  })

  it('ATTACH_ACCEPT 仅 Word/PDF', async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()
    expect(result.ATTACH_ACCEPT).toBe('.docx,.pdf')
    wrapper.unmount()
  })

  it('submit 走 FormData 并带 title/goal', async () => {
    vi.mocked(taskApi.submitTask).mockResolvedValue({ status: true, data: { id: 1, status: 'pending' } })
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = '校准'
    result.form.value.goal = '拖滑块'
    result.form.value.device_serial = 'S1'
    await result.submit()
    await flushPromises()

    expect(taskApi.submitTask).toHaveBeenCalledTimes(1)
    const fd = vi.mocked(taskApi.submitTask).mock.calls[0][0] as FormData
    expect(fd).toBeInstanceOf(FormData)
    expect(fd.get('title')).toBe('校准')
    expect(fd.get('goal')).toBe('拖滑块')
    expect(fd.get('device_serial')).toBe('S1')
    expect(fd.get('device_label')).toBe('M1')

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
