/**
 * [P0] 必测 — 访问凭证主动续期（单飞刷新）
 * 目录：tests/login/p0/
 *
 * 覆盖 specs/auth-session/spec.md 的「访问凭证在过期前主动续期」：
 * 未过期不续期、过期续期并写回、并发只刷一次、无续期凭证不发请求、解析不出的令牌按原样返回。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import {
  configureTokenRefresh,
  ensureFreshToken,
  isTokenExpired,
  refreshAccessToken,
  resetTokenRefreshLock,
  TOKEN_REFRESH_SKEW_SECONDS,
} from "@/shared/auth/token-refresh"
import type { AuthResponse } from "@/shared/types/auth"

/** 续期传输层的替身：生产环境由 api-client 注入真实 HTTP 请求 */
const refreshRequest = vi.fn<(refreshToken: string) => Promise<AuthResponse>>()

/** 造一个只含 exp 的假 JWT（不验签，测试只关心 exp 解码） */
function makeToken(expSecondsFromNow: number): string {
  const payload = { sub: "1", exp: Math.floor(Date.now() / 1000) + expSecondsFromNow }
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`
}

describe("[P0] 访问凭证主动续期", () => {
  beforeEach(() => {
    localStorage.clear()
    refreshRequest.mockReset()
    resetTokenRefreshLock()
    configureTokenRefresh(refreshRequest)
  })

  afterEach(() => {
    localStorage.clear()
  })

  it("凭证还有余量时不续期", async () => {
    const token = makeToken(3600)
    localStorage.setItem("access_token", token)
    localStorage.setItem("refresh_token", "refresh-1")

    await expect(ensureFreshToken()).resolves.toBe(token)
    expect(refreshRequest).not.toHaveBeenCalled()
  })

  it("凭证已过期时先续期并写回", async () => {
    localStorage.setItem("access_token", makeToken(-10))
    localStorage.setItem("refresh_token", "refresh-1")
    refreshRequest.mockResolvedValue({
      status: true,
      data: { access_token: "fresh-access", token_type: "bearer" },
    })

    await expect(ensureFreshToken()).resolves.toBe("fresh-access")
    expect(refreshRequest).toHaveBeenCalledTimes(1)
    expect(refreshRequest).toHaveBeenCalledWith("refresh-1")
    expect(localStorage.getItem("access_token")).toBe("fresh-access")
  })

  it("并发续期只发一次刷新请求", async () => {
    localStorage.setItem("access_token", makeToken(-10))
    localStorage.setItem("refresh_token", "refresh-1")
    refreshRequest.mockResolvedValue({ status: true, data: { access_token: "fresh-access" } })

    const [first, second] = await Promise.all([ensureFreshToken(), refreshAccessToken()])
    expect(first).toBe("fresh-access")
    expect(second).toBe("fresh-access")
    expect(refreshRequest).toHaveBeenCalledTimes(1)
  })

  it("没有续期凭证时不发刷新请求", async () => {
    const expired = makeToken(-10)
    localStorage.setItem("access_token", expired)

    await expect(ensureFreshToken()).resolves.toBe(expired)
    expect(refreshRequest).not.toHaveBeenCalled()
  })

  it("解析不出 exp 的令牌按当前凭证返回", async () => {
    localStorage.setItem("access_token", "not-a-jwt")
    localStorage.setItem("refresh_token", "refresh-1")

    await expect(ensureFreshToken()).resolves.toBe("not-a-jwt")
    expect(refreshRequest).not.toHaveBeenCalled()
  })

  it("临近过期的凭证（小于时钟偏差）也会续期", async () => {
    localStorage.setItem("access_token", makeToken(TOKEN_REFRESH_SKEW_SECONDS - 5))
    localStorage.setItem("refresh_token", "refresh-1")
    refreshRequest.mockResolvedValue({ status: true, data: { access_token: "fresh-access" } })

    await expect(ensureFreshToken()).resolves.toBe("fresh-access")
    expect(isTokenExpired(makeToken(3600))).toBe(false)
  })

  it("续期响应缺少访问凭证时抛出，且不写回", async () => {
    const expired = makeToken(-10)
    localStorage.setItem("access_token", expired)
    localStorage.setItem("refresh_token", "refresh-1")
    refreshRequest.mockResolvedValue({ status: false })

    await expect(refreshAccessToken()).rejects.toThrow()
    expect(localStorage.getItem("access_token")).toBe(expired)
  })
})
