/**
 * [P0] 平台工具调试 composable：schema 无 user_id、写工具确认取消不请求、非超管不可执行写
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import {
  displayResultJson,
  extractScreenshotPreview,
  useToolDebug,
} from '@/modules/ai-assistant/composables/useToolDebug'

vi.mock('element-plus', () => ({
  ElMessage: { warning: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

const fetchSchema = vi.fn()
const invokeTool = vi.fn()

vi.mock('@/modules/ai-assistant/api/toolbox', () => ({
  fetchPlatformToolSchema: (...args: unknown[]) => fetchSchema(...args),
  invokePlatformTool: (...args: unknown[]) => invokeTool(...args),
}))

import { ElMessage, ElMessageBox } from 'element-plus'

describe('tool debug helpers', () => {
  it('schema 展示结果时截图折叠 base64', () => {
    const result = {
      image: { base64: 'AAAA', media_type: 'image/jpeg' },
      summary: { serial: 'S1' },
    }
    const shot = extractScreenshotPreview(result)
    expect(shot?.dataUrl).toContain('data:image/jpeg;base64,AAAA')
    expect(displayResultJson(result)).toContain('S1')
    expect(displayResultJson(result)).not.toContain('AAAA')
  })
})

describe('useToolDebug', () => {
  beforeEach(() => {
    fetchSchema.mockReset()
    invokeTool.mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
    vi.mocked(ElMessage.error).mockReset()
  })

  it('加载 schema 后参数不含 user_id', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'acquire_device',
        summary: '锁定',
        read_only: false,
        parameters: [
          { name: 'serial', type: 'str', required: true },
          { name: 'timeout', type: 'int', required: false, default: 300 },
        ],
      },
    })
    const canWrite = ref(true)
    const { schema, loading } = useToolDebug(ref('acquire_device'), canWrite)
    await vi.waitFor(() => expect(loading.value).toBe(false))
    expect(schema.value?.parameters.every((p) => p.name !== 'user_id')).toBe(true)
  })

  it('非超管写工具 canExecute 为 false', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'acquire_device',
        summary: '锁定',
        read_only: false,
        parameters: [{ name: 'serial', type: 'str', required: true }],
      },
    })
    const { canExecute, loading } = useToolDebug(ref('acquire_device'), ref(false))
    await vi.waitFor(() => expect(loading.value).toBe(false))
    expect(canExecute.value).toBe(false)
  })

  it('写工具确认取消时不调用 invoke', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'release_device',
        summary: '释放',
        read_only: false,
        parameters: [{ name: 'serial', type: 'str', required: true }],
      },
    })
    vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')
    const { form, loading, runInvoke } = useToolDebug(ref('release_device'), ref(true))
    await vi.waitFor(() => expect(loading.value).toBe(false))
    form.value.serial = 'RF8'
    await runInvoke()
    expect(invokeTool).not.toHaveBeenCalled()
  })

  it('候选设备为空时仍可提交手输的值', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'swipe_screen',
        summary: '滑动',
        read_only: true,
        parameters: [
          { name: 'serial', type: 'str', required: true, options: [] },
          { name: 'direction', type: 'str', required: false, default: 'up' },
        ],
      },
    })
    invokeTool.mockResolvedValue({ status: true, data: { result: { ok: true } } })
    const { form, loading, runInvoke } = useToolDebug(ref('swipe_screen'), ref(false))
    await vi.waitFor(() => expect(loading.value).toBe(false))
    form.value.serial = 'RF8N21MSW7A'
    form.value.direction = 'down'
    await runInvoke()
    expect(invokeTool).toHaveBeenCalledWith('swipe_screen', {
      serial: 'RF8N21MSW7A',
      direction: 'down',
    })
  })

  it('invoke 失败时展示服务端 message 而非状态码原文', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'list_apps',
        summary: '列出已安装应用',
        read_only: true,
        parameters: [{ name: 'serial', type: 'str', required: true }],
      },
    })
    invokeTool.mockRejectedValue({
      response: {
        status: 500,
        data: { status: false, message: '工具执行失败: boom' },
      },
    })
    const { form, loading, runInvoke, invokeError } = useToolDebug(
      ref('list_apps'),
      ref(false),
    )
    await vi.waitFor(() => expect(loading.value).toBe(false))
    form.value.serial = 'RF8'
    await runInvoke()

    expect(invokeError.value).toBe('工具执行失败: boom')
    expect(ElMessage.error).toHaveBeenCalledWith('工具执行失败: boom')
  })

  it('本地缺必填参数仍提示本地文案，不被网络兜底覆盖', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'list_apps',
        summary: '列出已安装应用',
        read_only: true,
        parameters: [{ name: 'serial', type: 'str', required: true }],
      },
    })
    const { loading, runInvoke } = useToolDebug(ref('list_apps'), ref(false))
    await vi.waitFor(() => expect(loading.value).toBe(false))
    await runInvoke()

    expect(ElMessage.error).toHaveBeenCalledWith(expect.stringContaining('请填写必填参数'))
    expect(invokeTool).not.toHaveBeenCalled()
  })

  it('只读工具直接 invoke 无需确认', async () => {
    fetchSchema.mockResolvedValue({
      status: true,
      data: {
        name: 'list_devices',
        summary: '全部设备',
        read_only: true,
        parameters: [],
      },
    })
    invokeTool.mockResolvedValue({ status: true, data: { result: [] } })
    const { loading, runInvoke, result } = useToolDebug(ref('list_devices'), ref(false))
    await vi.waitFor(() => expect(loading.value).toBe(false))
    await runInvoke()
    expect(ElMessageBox.confirm).not.toHaveBeenCalled()
    expect(invokeTool).toHaveBeenCalledWith('list_devices', {})
    await nextTick()
    expect(result.value).toEqual([])
  })
})
