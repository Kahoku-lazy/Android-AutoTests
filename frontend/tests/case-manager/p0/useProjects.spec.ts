/**
 * [P0] useProjects — 空项目列表态
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import * as caseApi from '@/modules/case-manager/api'
import { useProjects } from '@/modules/case-manager/composables/useProjects'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('@/modules/case-manager/api', () => ({
  listProjects: vi.fn(),
  createProject: vi.fn(),
  deleteProject: vi.fn(),
}))

describe('[P0] useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loadProjects 成功后空列表触发 isEmpty', async () => {
    vi.mocked(caseApi.listProjects).mockResolvedValue({
      data: { status: true, data: [] },
    })

    const { result, wrapper } = await mountComposable(() => useProjects())
    await result.loadProjects()
    await flushPromises()

    expect(result.projects.value).toEqual([])
    expect(result.isEmpty.value).toBe(true)
    expect(result.loading.value).toBe(false)

    wrapper.unmount()
  })

  it('loadProjects 返回项目时 isEmpty 为 false', async () => {
    vi.mocked(caseApi.listProjects).mockResolvedValue({
      data: {
        status: true,
        data: [
          {
            id: 1,
            name: '制冰机',
            description: '',
            created_by: '1',
            created_at: '2026-09-09T12:00:00',
            updated_at: '2026-09-09T12:00:00',
            case_count: 3,
          },
        ],
      },
    })

    const { result, wrapper } = await mountComposable(() => useProjects())
    await result.loadProjects()
    await flushPromises()

    expect(result.projects.value).toHaveLength(1)
    expect(result.isEmpty.value).toBe(false)

    wrapper.unmount()
  })
})
