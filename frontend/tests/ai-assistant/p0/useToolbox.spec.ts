/**
 * [P0] 自定义 Skill 文件夹上传：files/paths 一一对应、失败原因透出、成功后刷新目录
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

// 组件外调用 onMounted 不会执行，这里直接执行，以便断言「上传成功后刷新目录」
vi.mock('vue', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue')>()
  return { ...actual, onMounted: (fn: () => void) => fn() }
})

const post = vi.fn()
const get = vi.fn()

// 只替换 HTTP 出口；formatApiError 取真实实现（错误文案透出正是走它），
// 不用 importOriginal 的部分 mock，避免与真实模块初始化相互依赖
vi.mock('@/shared/api-client', async () => {
  const errors = await import('@/shared/types/api-error')
  return {
    default: {
      post: (...args: unknown[]) => post(...args),
      get: (...args: unknown[]) => get(...args),
    },
    formatApiError: errors.formatApiError,
  }
})

import { ElMessage } from 'element-plus'
import { uploadSharedSkill } from '@/modules/ai-assistant/api/toolbox'
import { useToolbox } from '@/modules/ai-assistant/composables/useToolbox'

function folderFile(relPath: string, content = 'x'): File {
  const fileName = relPath.split('/').pop() as string
  const file = new File([content], fileName)
  Object.defineProperty(file, 'webkitRelativePath', { value: relPath })
  return file
}

function filePickEvent(files: File[]): Event {
  return { target: { files, value: 'C:/fakepath/demo-skill' } } as unknown as Event
}

describe('uploadSharedSkill', () => {
  beforeEach(() => {
    post.mockReset()
    get.mockReset()
  })

  it('同时提交 files 与 paths，且顺序一一对应', async () => {
    post.mockResolvedValue({ data: { status: true, data: { id: 7 } } })

    await uploadSharedSkill(
      [folderFile('demo-skill/SKILL.md'), folderFile('demo-skill/references/a.md')],
      'demo-skill',
    )

    const [url, body] = post.mock.calls[0]
    expect(url).toBe('/ai/toolbox/upload-skill/')
    const formData = body as FormData
    expect(formData.getAll('name')).toEqual(['demo-skill'])
    expect(formData.getAll('paths')).toEqual([
      'demo-skill/SKILL.md',
      'demo-skill/references/a.md',
    ])
    expect(formData.getAll('files').length).toBe(formData.getAll('paths').length)
  })
})

describe('useToolbox 上传反馈', () => {
  beforeEach(() => {
    post.mockReset()
    get.mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    get.mockResolvedValue({ data: { status: true, data: { items: [] } } })
  })

  it('上传失败时展示服务端 message 而不是通用文案', async () => {
    const message = '已存在同名 skill 文件夹: demo-skill'
    post.mockRejectedValue({ response: { status: 400, data: { status: false, message } } })

    const { onSkillFolderPicked } = useToolbox()
    await onSkillFolderPicked(filePickEvent([folderFile('demo-skill/SKILL.md')]))

    expect(ElMessage.error).toHaveBeenCalledWith(message)
    expect(ElMessage.error).not.toHaveBeenCalledWith('上传失败')
  })

  it('上传成功后给出成功反馈并刷新目录', async () => {
    post.mockResolvedValue({ data: { status: true, data: { id: 7 } } })
    get
      .mockResolvedValueOnce({ data: { status: true, data: { items: [] } } })
      .mockResolvedValueOnce({
        data: {
          status: true,
          data: { items: [{ id: 7, name: 'demo-skill', item_type: 'skill' }] },
        },
      })

    const { items, onSkillFolderPicked } = useToolbox()
    await onSkillFolderPicked(filePickEvent([folderFile('demo-skill/SKILL.md')]))

    expect(ElMessage.success).toHaveBeenCalledWith('Skill 文件夹已上传')
    expect(items.value.map((item) => item.name)).toEqual(['demo-skill'])
  })
})
