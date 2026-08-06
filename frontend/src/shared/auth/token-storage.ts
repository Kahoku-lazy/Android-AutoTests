/** token-storage — 多账号 token 存储的唯一真相源。
 *
 *  api-client 和 useAuthPool.ts 都从这里读写，消除双源竞态。
 *
 *  存储格式：
 *    localStorage.auth_accounts  = { admin: {access_token, refresh_token}, ... }
 *    sessionStorage.auth_active  = "admin"  (per-tab 隔离)
 */

import type { AuthPool } from "@/shared/types/auth"

export const POOL_KEY = "auth_accounts"
const ACTIVE_KEY = "auth_active"

// ── 纯函数：底层存储读写 ──

export function readPool(): AuthPool {
  // 兼容旧单 token 格式迁移
  const oldToken = localStorage.getItem("access_token")
  if (oldToken) {
    const oldRefresh = localStorage.getItem("refresh_token") || ""
    const oldUser = localStorage.getItem("username") || "admin"
    const pool: AuthPool = { [oldUser]: { access_token: oldToken, refresh_token: oldRefresh } }
    localStorage.setItem(POOL_KEY, JSON.stringify(pool))
    sessionStorage.setItem(ACTIVE_KEY, oldUser)
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("username")
    return pool
  }
  try {
    return JSON.parse(localStorage.getItem(POOL_KEY) || "{}")
  } catch {
    return {}
  }
}

export function writePool(pool: AuthPool): void {
  localStorage.setItem(POOL_KEY, JSON.stringify(pool))
}

export function getActive(): string {
  const pool = readPool()
  const active = sessionStorage.getItem(ACTIVE_KEY) || Object.keys(pool)[0] || ""
  // 确保 active 账号仍在池中
  if (active && !pool[active]) {
    const first = Object.keys(pool)[0] || ""
    sessionStorage.setItem(ACTIVE_KEY, first)
    return first
  }
  return active
}

export function setActive(username: string): void {
  sessionStorage.setItem(ACTIVE_KEY, username)
}

// ── 便捷函数：给 api-client 用 ──

export function getToken(): string {
  const pool = readPool()
  const active = getActive()
  return pool[active]?.access_token || ""
}

export function setToken(token: string): void {
  const pool = readPool()
  const active = getActive()
  if (active && pool[active]) {
    pool[active].access_token = token
    writePool(pool)
  }
}

export function clearToken(): void {
  const pool = readPool()
  const active = getActive()
  if (active) {
    delete pool[active]
    writePool(pool)
    const remaining = Object.keys(pool)
    setActive(remaining.length > 0 ? remaining[0] : "")
  }
}

export function getRefreshToken(): string {
  const pool = readPool()
  const active = getActive()
  return pool[active]?.refresh_token || ""
}

export function getActiveUsername(): string {
  return sessionStorage.getItem(ACTIVE_KEY) || ""
}
