import { beforeEach, describe, expect, it, vi } from "vitest"
import type { AxiosError, InternalAxiosRequestConfig } from "axios"
import { createAuthInterceptors } from "@/shared/api-auth-interceptors"
import { resetAccountDisabledCountdown } from "@/shared/auth/account-disabled"
import {
  ACCOUNT_DISABLED_CODE,
  ACCOUNT_DISABLED_SECONDS,
} from "@/shared/auth/account-disabled.constants"

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
  const refreshRequest = vi.fn()
  const redirectToLogin = vi.fn()
  const retryRequest = vi.fn()

  let interceptors: ReturnType<typeof createAuthInterceptors>

  beforeEach(() => {
    vi.clearAllMocks()
    getToken.mockReturnValue("old-access")
    getRefreshToken.mockReturnValue("valid-refresh")
    resetAccountDisabledCountdown()
    vi.useRealTimers()
    interceptors = createAuthInterceptors({
      getToken,
      setToken,
      clearToken,
      getRefreshToken,
      refreshRequest,
      redirectToLogin,
      retryRequest,
    })
  })

  it("请求拦截器：注入 Bearer token", () => {
    const config = { headers: {} } as InternalAxiosRequestConfig
    const next = interceptors.authRequestInterceptor(config)
    expect(next.headers.Authorization).toBe("Bearer old-access")
  })

  it("无 token 时：不写 Authorization", () => {
    getToken.mockReturnValue("")
    const config = { headers: {} } as InternalAxiosRequestConfig
    interceptors.authRequestInterceptor(config)
    expect(config.headers.Authorization).toBeUndefined()
  })

  it("停用专用拒绝：有 refresh 也不续期，10 秒后清会话", async () => {
    vi.useFakeTimers()
    const config = { headers: {}, url: "/dashboard/stats/" } as InternalAxiosRequestConfig
    const err = {
      isAxiosError: true,
      name: "AxiosError",
      message: "disabled",
      response: {
        status: 403,
        statusText: "Forbidden",
        data: { status: false, code: ACCOUNT_DISABLED_CODE, message: "停用" },
        headers: {},
        config,
      },
      config,
      toJSON: () => ({}),
    } as AxiosError

    await expect(interceptors.authErrorInterceptor(err)).rejects.toBe(err)
    await expect(interceptors.authErrorInterceptor(err)).rejects.toBe(err)
    expect(refreshRequest).not.toHaveBeenCalled()
    expect(retryRequest).not.toHaveBeenCalled()
    expect(clearToken).not.toHaveBeenCalled()

    vi.advanceTimersByTime(ACCOUNT_DISABLED_SECONDS * 1000)
    expect(clearToken).toHaveBeenCalledTimes(1)
    expect(redirectToLogin).toHaveBeenCalledTimes(1)
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

  it("并发两个 401：只触发一次 refresh", async () => {
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

  it("refresh 失败：清 token 并跳转 /login", async () => {
    refreshRequest.mockRejectedValue(new Error("refresh failed"))
    const config = { headers: {}, url: "/x" } as InternalAxiosRequestConfig

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(clearToken).toHaveBeenCalled()
    expect(redirectToLogin).toHaveBeenCalled()
    expect(retryRequest).not.toHaveBeenCalled()
  })

  it("无 refresh_token 时：直接拒绝，不跳转", async () => {
    getRefreshToken.mockReturnValue("")
    const config = { headers: {}, url: "/x" } as InternalAxiosRequestConfig

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(refreshRequest).not.toHaveBeenCalled()
    expect(redirectToLogin).not.toHaveBeenCalled()
  })

  it("同一请求已 _retry 过：不再 refresh", async () => {
    const config = { headers: {}, url: "/x", _retry: true } as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    await expect(interceptors.authErrorInterceptor(make401(config))).rejects.toBeTruthy()

    expect(refreshRequest).not.toHaveBeenCalled()
  })
})
