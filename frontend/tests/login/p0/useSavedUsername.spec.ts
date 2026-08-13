/**
 * [P0] 必测 — 记住账号 localStorage 读写
 * 目录：tests/login/p0/
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { useSavedUsername } from '@/views/composables/useSavedUsername'

const KEY = 'saved_username'

describe('[P0] useSavedUsername', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('无缓存时用户名为空，记住账号为 false', () => {
    const { loginUsername, rememberMe } = useSavedUsername()
    expect(loginUsername.value).toBe('')
    expect(rememberMe.value).toBe(false)
  })

  it('有缓存时预填用户名，并开启记住账号', () => {
    localStorage.setItem(KEY, 'alice')
    const { loginUsername, rememberMe } = useSavedUsername()
    expect(loginUsername.value).toBe('alice')
    expect(rememberMe.value).toBe(true)
  })

  it('勾选记住账号时，saveUsername 写入 localStorage', () => {
    const { rememberMe, saveUsername } = useSavedUsername()
    rememberMe.value = true
    saveUsername('bob')
    expect(localStorage.getItem(KEY)).toBe('bob')
  })

  it('未勾选记住账号时，saveUsername 清除 localStorage', () => {
    localStorage.setItem(KEY, 'old')
    const { rememberMe, saveUsername } = useSavedUsername()
    rememberMe.value = false
    saveUsername('bob')
    expect(localStorage.getItem(KEY)).toBeNull()
  })
})
