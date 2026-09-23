/** token-storage — 单账号会话存储的唯一真相源。
 *
 *  api-client 与页面都从这里读写，避免双源竞态。
 *
 *  存储格式：
 *    localStorage.access_token  = "<jwt>"
 *    localStorage.refresh_token = "<jwt>"
 *    localStorage.username      = "<账号名>"
 */

const ACCESS_KEY = "access_token"
const REFRESH_KEY = "refresh_token"
const USERNAME_KEY = "username"

/** 多账号时代遗留的账号池键：写入新会话时顺带清掉，避免残留结构与新键长期并存 */
const LEGACY_POOL_KEY = "auth_accounts"

// ── 会话读取 ──

export function getToken(): string {
  return localStorage.getItem(ACCESS_KEY) || ""
}

export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_KEY) || ""
}

export function getUsername(): string {
  return localStorage.getItem(USERNAME_KEY) || ""
}

// ── 会话写入 ──

/** 登录/注册成功后写入整个会话（一次只保留一个账号） */
export function saveSession(username: string, access_token: string, refresh_token: string): void {
  localStorage.setItem(ACCESS_KEY, access_token)
  localStorage.setItem(REFRESH_KEY, refresh_token)
  localStorage.setItem(USERNAME_KEY, username)
  localStorage.removeItem(LEGACY_POOL_KEY)
}

/** 续期成功后只轮换 access，不动账号名与 refresh */
export function setToken(token: string): void {
  localStorage.setItem(ACCESS_KEY, token)
}

/** 登出/续期失败时清空整个会话 */
export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

/** 拦截器沿用 clearToken 这个名字；语义与 clearSession 相同 */
export const clearToken = clearSession
