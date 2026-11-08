/**
 * 访问凭证的主动续期：HTTP 401 与 WebSocket 4401 共用同一把「单飞」锁。
 *
 * 业务：
 * 1. 只解码 JWT 的 exp 判断是否过期，不做验签（验签是服务端的事）。
 * 2. 已过期或即将过期时先用 refresh 换新 access，再交给调用方使用。
 * 3. 同一时刻的并发续期只发一次 POST /api/auth/refresh/。
 */
import { getRefreshToken, getToken, setToken } from "@/shared/auth/token-storage"
import type { AuthResponse } from "@/shared/types/auth"

/** 提前续期的时钟偏差（秒）：剩不到一分钟就当已过期 */
export const TOKEN_REFRESH_SKEW_SECONDS = 60

/** 续期传输层：由 api-client 注入，避免本模块直接依赖 axios（HTTP 唯一出口约束） */
export type RefreshRequest = (refreshToken: string) => Promise<AuthResponse>

let transport: RefreshRequest | null = null

/**
 * 注入续期传输层。
 *
 * Args:
 *   request: 用续期凭证换 AuthResponse 的函数；生产实现见 `shared/api-client.ts`。
 */
export function configureTokenRefresh(request: RefreshRequest): void {
  transport = request
}

/** 单飞锁：并发续期共用同一个 Promise，结束后清空 */
let inFlight: Promise<string> | null = null

/** 把 JWT 的 payload 段解出来；格式不合法返回 null（不验签） */
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

/**
 * 取令牌的过期时刻（Unix 秒）。
 *
 * Args:
 *   token: JWT 字符串。
 *
 * Returns:
 *   过期时刻；解析不出 exp 时返回 null（交由 401 / 4401 兜底）。
 */
export function tokenExpiresAt(token: string): number | null {
  const payload = decodePayload(token)
  const exp = payload?.exp
  return typeof exp === "number" && Number.isFinite(exp) ? exp : null
}

/**
 * 令牌是否已过期（含时钟偏差）。
 *
 * Args:
 *   token: 待判断的令牌。
 *   skewSeconds: 提前量，默认 60 秒。
 *
 * Returns:
 *   true 表示应当续期；解析不出 exp 时返回 false，避免误判。
 */
export function isTokenExpired(
  token: string,
  skewSeconds: number = TOKEN_REFRESH_SKEW_SECONDS,
): boolean {
  const expiresAt = tokenExpiresAt(token)
  if (expiresAt === null) return false
  return Date.now() / 1000 + skewSeconds >= expiresAt
}

/**
 * 用续期凭证换一个新的访问凭证（单飞）。
 *
 * Raises:
 *   Error: 续期通道未初始化、没有续期凭证，或续期接口返回失败。
 *
 * Returns:
 *   新的访问凭证。
 */
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

/**
 * 确保拿到一个可用的访问凭证：过期（或即将过期）才续期。
 *
 * Args:
 *   minTtlSeconds: 剩余寿命低于该值即视为需要续期，默认 60 秒。
 *
 * Returns:
 *   可用的访问凭证；本地没有凭证、没有续期凭证或解析不出 exp 时，
 *   原样返回当前凭证，由下游的 401 / 4401 走各自的失败路径。
 */
export async function ensureFreshToken(
  minTtlSeconds: number = TOKEN_REFRESH_SKEW_SECONDS,
): Promise<string> {
  const token = getToken()
  if (!token) return ""
  if (!isTokenExpired(token, minTtlSeconds)) return token
  if (!getRefreshToken()) return token
  return refreshAccessToken()
}

/** 仅测试用：清空单飞锁 */
export function resetTokenRefreshLock(): void {
  inFlight = null
}
