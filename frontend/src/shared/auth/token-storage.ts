/**
 * 当前登录会话：账号、访问凭证、续期凭证。一次只保留一个账号。
 *
 * 业务：
 * - 读取当前账号、访问凭证和续期凭证
 * - 登录或注册成功后写入整段会话
 * - 续期成功后只更换访问凭证
 * - 登出或续期失败时清空会话
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
