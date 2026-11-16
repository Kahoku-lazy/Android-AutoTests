/**
 * [P0] 必测 — 用户管理列表的分页与筛选契约（spec: ops-user-console）
 *
 * 目录：tests/ops-console/p0/
 * 断言：① 首次加载请求第 1 页与默认每页条数；② 切状态筛选回到第 1 页并带上 active；
 * ③ 翻页请求目标页；④ 改每页条数回到第 1 页；⑤ 失败时给出错误文案且不清空已加载数据。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useOpsUsers } from '@/modules/ops-console/composables/useOpsUsers'
import { listOpsUsers } from '@/modules/ops-console/api'
import type { OpsUser, OpsUserPage } from '@/modules/ops-console/types'

vi.mock('@/modules/ops-console/api', () => ({
  listOpsUsers: vi.fn(),
}))

const mockedList = vi.mocked(listOpsUsers)

function ok(page: Partial<OpsUserPage> = {}) {
  const data: OpsUserPage = { users: [], total: 0, page: 1, page_size: 20, ...page }
  return { data: { status: true, data } }
}

function user(id: number, username: string): OpsUser {
  return {
    id,
    username,
    email: `${username}@example.com`,
    identity: 'user',
    is_active: true,
    date_joined: '2026-11-01 10:00',
    last_login: '',
  }
}

beforeEach(() => {
  mockedList.mockReset()
})

describe('[P0] useOpsUsers', () => {
  it('首次加载请求第 1 页与默认每页条数', async () => {
    mockedList.mockResolvedValue(ok())
    const state = useOpsUsers()

    await state.load()

    expect(mockedList).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      keyword: undefined,
      active: undefined,
    })
  })

  it('切到「停用」筛选会回到第 1 页并带上 active=false', async () => {
    mockedList.mockResolvedValue(ok())
    const state = useOpsUsers()
    state.page.value = 3

    state.setStatus('inactive')
    await Promise.resolve()

    expect(state.page.value).toBe(1)
    expect(mockedList).toHaveBeenLastCalledWith({
      page: 1,
      page_size: 20,
      keyword: undefined,
      active: 'false',
    })
  })

  it('翻页请求目标页，越界被夹到最后一页', async () => {
    mockedList.mockResolvedValue(ok({ total: 45 }))
    const state = useOpsUsers()
    await state.load()

    state.goPage(2)
    await Promise.resolve()
    expect(state.page.value).toBe(2)

    state.goPage(99)
    await Promise.resolve()
    expect(state.page.value).toBe(3)
  })

  it('改每页条数会回到第 1 页', async () => {
    mockedList.mockResolvedValue(ok())
    const state = useOpsUsers()
    state.page.value = 2

    state.setPageSize(50)
    await Promise.resolve()

    expect(state.page.value).toBe(1)
    expect(mockedList).toHaveBeenLastCalledWith({
      page: 1,
      page_size: 50,
      keyword: undefined,
      active: undefined,
    })
  })

  it('加载成功后写入账号，空列表进入空态', async () => {
    mockedList.mockResolvedValue(ok({ users: [user(1, 'alice')], total: 1 }))
    const state = useOpsUsers()
    await state.load()

    expect(state.users.value.map((item) => item.username)).toEqual(['alice'])
    expect(state.showEmpty.value).toBe(false)

    mockedList.mockResolvedValue(ok({ users: [], total: 0 }))
    await state.load()
    expect(state.showEmpty.value).toBe(true)
  })

  it('加载失败时给出错误文案，且不清空已加载数据', async () => {
    mockedList.mockResolvedValue(ok({ users: [user(1, 'alice')], total: 1 }))
    const state = useOpsUsers()
    await state.load()

    mockedList.mockRejectedValueOnce({ response: { status: 403, data: { message: '仅运营可访问' } } })
    await state.load()

    expect(state.error.value).toBe('仅运营可访问')
    expect(state.users.value).toHaveLength(1)
  })
})
