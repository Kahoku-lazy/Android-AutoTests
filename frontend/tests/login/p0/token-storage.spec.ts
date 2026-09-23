/**
 * [P0] 必测 — 单账号会话存储
 * 目录：tests/login/p0/
 */
import { beforeEach, describe, expect, it } from 'vitest'
import {
  clearSession,
  getRefreshToken,
  getToken,
  getUsername,
  saveSession,
} from '@/shared/auth/token-storage'

describe('[P0] token-storage 单账号会话', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('saveSession：写入后三项都能读回', () => {
    saveSession('alice', 'access-1', 'refresh-1')

    expect(getToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')
    expect(getUsername()).toBe('alice')
  })

  it('二次 saveSession：覆盖原账号而不是并存', () => {
    saveSession('alice', 'a1', 'r1')
    saveSession('bob', 'a2', 'r2')

    expect(getUsername()).toBe('bob')
    expect(getToken()).toBe('a2')
    expect(getRefreshToken()).toBe('r2')
    // 单账号：本地不存在账号列表结构
    expect(Object.keys(localStorage).sort()).toEqual(['access_token', 'refresh_token', 'username'])
  })

  it('clearSession：三项一起清空', () => {
    saveSession('alice', 'a1', 'r1')
    clearSession()

    expect(getToken()).toBe('')
    expect(getRefreshToken()).toBe('')
    expect(getUsername()).toBe('')
    expect(localStorage.length).toBe(0)
  })

  it('saveSession：清掉多账号时代残留的 auth_accounts', () => {
    localStorage.setItem(
      'auth_accounts',
      JSON.stringify({ alice: { access_token: 'a', refresh_token: 'r' } }),
    )
    saveSession('alice', 'a1', 'r1')

    expect(localStorage.getItem('auth_accounts')).toBeNull()
  })
})
