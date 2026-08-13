/**
 * [P0] 必测 — 多账号 token 池
 * 目录：tests/login/p0/
 */
/**
 * [P0] 必测 — 多账号 token 池
 * 目录：tests/login/p0/
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthPool } from '@/shared/composables/useAuthPool'
import { POOL_KEY } from '@/shared/auth/token-storage'
import { clearAuthStorage, mountComposable } from '../../helpers/mountComposable'

describe('[P0] useAuthPool', () => {
  beforeEach(() => {
    clearAuthStorage()
  })

  it('空池时账号列表为空', async () => {
    const { result } = await mountComposable(() => useAuthPool())
    expect(result.accountList.value).toEqual([])
    expect(result.activeAccount.value).toBe('')
  })

  it('loginAccount 写入池并设为 active', async () => {
    const { result } = await mountComposable(() => useAuthPool())
    result.loginAccount('alice', 'access', 'refresh')

    expect(result.accountList.value).toEqual(['alice'])
    expect(result.activeAccount.value).toBe('alice')
    expect(JSON.parse(localStorage.getItem(POOL_KEY)!).alice.access_token).toBe('access')
    expect(sessionStorage.getItem('auth_active')).toBe('alice')
  })

  it('switchAccount 对存在账号返回 true', async () => {
    const { result } = await mountComposable(() => useAuthPool())
    result.loginAccount('alice', 'a', 'r')
    result.loginAccount('bob', 'b', 'r')

    expect(result.switchAccount('alice')).toBe(true)
    expect(sessionStorage.getItem('auth_active')).toBe('alice')
    expect(result.switchAccount('ghost')).toBe(false)
  })

  it('logoutAccount 有剩余账号时切到下一个', async () => {
    const { result } = await mountComposable(() => useAuthPool())
    result.loginAccount('alice', 'a', 'r')
    result.loginAccount('bob', 'b', 'r')
    // bob 是 active
    expect(result.logoutAccount()).toBe(true)
    expect(result.accountList.value).toEqual(['alice'])
    expect(result.activeAccount.value).toBe('alice')
  })

  it('logoutAccount 无剩余账号时返回 false', async () => {
    const { result } = await mountComposable(() => useAuthPool())
    result.loginAccount('alice', 'a', 'r')
    expect(result.logoutAccount()).toBe(false)
    expect(result.accountList.value).toEqual([])
    expect(result.activeAccount.value).toBe('')
  })
})
