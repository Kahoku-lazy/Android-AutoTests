const ACCESS_KEY = "access_token"
const REFRESH_KEY = "refresh_token"
const USERNAME_KEY = "username"

const LEGACY_POOL_KEY = "auth_accounts"

export function getToken(): string {
  return localStorage.getItem(ACCESS_KEY) || ""
}

export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_KEY) || ""
}

export function getUsername(): string {
  return localStorage.getItem(USERNAME_KEY) || ""
}

export function saveSession(username: string, access_token: string, refresh_token: string): void {
  localStorage.setItem(ACCESS_KEY, access_token)
  localStorage.setItem(REFRESH_KEY, refresh_token)
  localStorage.setItem(USERNAME_KEY, username)
  localStorage.removeItem(LEGACY_POOL_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(ACCESS_KEY, token)
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

export const clearToken = clearSession
