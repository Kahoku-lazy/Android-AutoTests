/**
 * [P0] 必测 — api-client 鉴权拦截器（并发 refresh / 重试 / 多账号失败）
 * 目录：tests/login/p0/
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import type { AxiosError, InternalAxiosRequestConfig } from "axios"
import { createAuthInterceptors } from "@/shared/api-auth-interceptors"

function make401(config: InternalAxiosRequestConfig): AxiosError {
  return {
    isAxiosError: true,
    name: "AxiosError",
    message: "Request failed with status code 401",
    response: {
      status: 401,
      statusText: "Unauthorized",
      data: { status: false, message: "Invalid or expired token" },
      headers: {},
      config,
    },
    config,
    toJSON: () => ({}),
  } as AxiosError
}

describe("[P0] createAuthInterceptors", () => {
  const getToken = vi.fn(() => "old-access")
  const setToken = vi.fn()
  const clearToken = vi.fn()
  const getRefreshToken = vi.fn(() => "valid-refresh")
  const getActive = vi.fn(() => "")
  const refreshRequest = vi.fn()
  const redirectToLogin = vi.fn()
  const retryRequest = vi.fn()

  let interceptors: ReturnType<typeof createAuthInterceptors>

  beforeEach(() => {
    vi.clearAllMocks()
    getToken.mockReturnValue("old-access")
    getRefreshToken.mockReturnValue("valid-refresh")
    getActive.mockReturnValue("")
    interceptors = createAuthInterceptors({
      getToken,
      setToken,
      clearToken,
      getRefreshToken,
      getActive,
      refreshRequest,
      redirectToLogin,
      retryRequest,
    })
  })

  it("请求拦截器注入 Bearer token", () => {
    const config = { headers: {} } as InternalAxiosRequestConfig
    const next = interceptors.authRequestInterceptor(config)
    expect(next.headers.Authorization).toBe("Bearer old-access")
  })

  it("无 token 时不写 Authorization", () => {
    getToken.mockReturnValue("")
    const config = { headers: {} } as InternalAxiosRequestConfig
    interceptors.authRequestInterceptor(config)
    expect(config.headers.Authorization).toBeUndefined()
  })

  it("401 后 refresh 成功：写新 token 并重试原请求", async () => {
    const config = { headers: {}, url: "/dashboard/stats/" } as InternalAxiosRequestConfig
    refreshRequest.mockResolvedValue({
      data: {
        status: true,
        data: {
          access_token: "new-access",
          token_type: "bearer",
        },
      },
    })
    retryRequest.mockResolvedValue({ data: { status: true } })

    const result = await interceptors.authErrorInterceptor(make401(config))

    expect(refreshRequest).toHaveBeenCalledTimes(1)
    expect(refreshRequest).toHaveBeenCalledWith({ refresh_token: "valid-refresh" })
    expect(setToken).toHaveBeenCalledWith("new-access")
    expect(config.headers.Authorization).toBe("Bearer new-access")
    expect(retryRequest).toHaveBeenCalledWith(config)
    expect(result).toEqual({ data: { status: true } })
    expect(redirectToLogin).not.toHaveBeenCalled()
  })

  it("并发两个 401 只触发一次 refresh", async () => {
    let resolveRefresh!: (v: {
      data: {
        status: true
        data: { access_token: string; token_type: string }
      }
    }) => void
    refreshRequest.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve
        }),
    )
    retryRequest.mockResolvedValue({ data: { ok: true } })

    const c1 = { headers: {}, url: "/a" } as InternalAxiosRequestConfig
    const c2 = { headers: {}, url: "/b" } as InternalAxiosRequestConfig

    const p1 = interceptors.authErrorInterceptor(make401(c1))
    const p2 = interceptors.authErrorInterceptor(make401(c2))

    expect(interceptors.hasInFlightRefresh()).toBe(true)
    expect(refreshRequest).toHaveBeenCalledTimes(1)

    resolveRefresh({
      data: {
        status: true,
        data: { access_token: "shared-new", token_type: "bearer" },
      },
    })
    await Promise.all([p1, p2])

    expect(refreshRequest).toHaveBeenCalledTimes(1)
    expect(setToken).toHaveBeenCalledWith("shared-new")
    expect(retryRequest).toHaveBeenCalledTimes(2)
  })

  it("refresh 失败且无剩余账号：清 token 并跳转 /login", async () => {
    getActive.mockReturnValue("")
    refreshRequest.mockRejectedValue(new Error("refresh failed"))
    const config = { headers: {}, url: "/x" } as InternalAxiosRequestConfig

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(clearToken).toHaveBeenCalled()
    expect(redirectToLogin).toHaveBeenCalled()
    expect(retryRequest).not.toHaveBeenCalled()
  })

  it("refresh 失败但仍有剩余账号：清当前账号，不跳转登录", async () => {
    getActive.mockReturnValue("bob")
    refreshRequest.mockRejectedValue(new Error("refresh failed"))
    const config = { headers: {}, url: "/x" } as InternalAxiosRequestConfig

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(clearToken).toHaveBeenCalled()
    expect(redirectToLogin).not.toHaveBeenCalled()
  })

  it("无 refresh_token 时直接拒绝，不跳转", async () => {
    getRefreshToken.mockReturnValue("")
    const config = { headers: {}, url: "/x" } as InternalAxiosRequestConfig

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(refreshRequest).not.toHaveBeenCalled()
    expect(redirectToLogin).not.toHaveBeenCalled()
  })

  it("同一请求已 _retry 过则不再 refresh", async () => {
    const config = { headers: {}, url: "/x", _retry: true } as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(refreshRequest).not.toHaveBeenCalled()
  })
})
