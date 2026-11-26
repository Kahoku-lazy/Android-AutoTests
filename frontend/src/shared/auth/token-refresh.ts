import { getRefreshToken, getToken, setToken } from "@/shared/auth/token-storage"
import type { AuthResponse } from "@/shared/types/auth"

export const TOKEN_REFRESH_SKEW_SECONDS = 60

export type RefreshRequest = (refreshToken: string) => Promise<AuthResponse>

let transport: RefreshRequest | null = null

export function configureTokenRefresh(request: RefreshRequest): void {
  transport = request
}

let inFlight: Promise<string> | null = null

function decodePayload(token: string): Record<string, unknown> | null {
  const segment = token.split(".")[1]
  if (!segment) return null
  try {
    const normalized = segment.replace(/-/g, "+").replace(/_/g, "/")
    const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4)
    const raw = atob(padded)
    const bytes = Uint8Array.from(raw, (char) => char.charCodeAt(0))
    return JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>
  } catch {
    return null
  }
}

export function tokenExpiresAt(token: string): number | null {
  const payload = decodePayload(token)
  const exp = payload?.exp
  return typeof exp === "number" && Number.isFinite(exp) ? exp : null
}

export function isTokenExpired(
  token: string,
  skewSeconds: number = TOKEN_REFRESH_SKEW_SECONDS,
): boolean {
  const expiresAt = tokenExpiresAt(token)
  if (expiresAt === null) return false
  return Date.now() / 1000 + skewSeconds >= expiresAt
}

export function refreshAccessToken(): Promise<string> {
  if (inFlight) return inFlight

  const refreshToken = getRefreshToken()
  if (!refreshToken) return Promise.reject(new Error("缺少续期凭证"))
  if (!transport) return Promise.reject(new Error("续期通道未初始化"))

  inFlight = transport(refreshToken)
    .then((body) => {
      const data = body?.data as { access_token?: string } | undefined
      const access = data?.access_token
      if (!body?.status || !access) throw new Error("续期响应缺少访问凭证")
      setToken(access)
      return access
    })
    .finally(() => {
      inFlight = null
    })

  return inFlight
}

export async function ensureFreshToken(
  minTtlSeconds: number = TOKEN_REFRESH_SKEW_SECONDS,
): Promise<string> {
  const token = getToken()
  if (!token) return ""
  if (!isTokenExpired(token, minTtlSeconds)) return token
  if (!getRefreshToken()) return token
  return refreshAccessToken()
}

export function resetTokenRefreshLock(): void {
  inFlight = null
}
