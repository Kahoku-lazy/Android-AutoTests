/**
 * api-auth-interceptors — 可注入依赖的鉴权拦截器，便于单测。
 *
 * api-client.ts 注入真实 token-storage / axios；测试注入 mock。
 */
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios"
import type { AuthResponse } from "@/shared/types/auth"

export interface AuthInterceptorDeps {
  getToken: () => string
  setToken: (token: string) => void
  clearToken: () => void
  getRefreshToken: () => string
  getActive: () => string
  /** 刷新请求（生产用 axios.post，测试可 mock） */
  refreshRequest: (body: { refresh_token: string }) => Promise<{ data: AuthResponse }>
  /** 无剩余账号时跳转登录 */
  redirectToLogin: () => void
  /** 用新 token 重试原请求 */
  retryRequest: (config: InternalAxiosRequestConfig) => Promise<unknown>
}

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

export interface AuthInterceptors {
  authRequestInterceptor: (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig
  authErrorInterceptor: (err: AxiosError) => Promise<unknown>
  /** 仅测试用：清空并发 refresh 锁 */
  resetRefreshLock: () => void
  /** 仅测试用：当前是否有 in-flight refresh */
  hasInFlightRefresh: () => boolean
}

export function createAuthInterceptors(deps: AuthInterceptorDeps): AuthInterceptors {
  let refreshPromise: Promise<{ data: AuthResponse }> | null = null

  function authRequestInterceptor(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    const token = deps.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }

  async function authErrorInterceptor(err: AxiosError): Promise<unknown> {
    const originalRequest = err.config as RetryableRequest | undefined
    if (err.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const currentRefreshToken = deps.getRefreshToken()
      if (currentRefreshToken) {
        originalRequest._retry = true
        try {
          if (!refreshPromise) {
            refreshPromise = deps
              .refreshRequest({ refresh_token: currentRefreshToken })
              .finally(() => {
                refreshPromise = null
              })
          }
          const resp = await refreshPromise
          if (resp.data.status === true) {
            const access = resp.data.data.access_token
            deps.setToken(access)
            originalRequest.headers.Authorization = `Bearer ${access}`
            return deps.retryRequest(originalRequest)
          }
          refreshPromise = null
        } catch {
          refreshPromise = null
          deps.clearToken()
          const active = deps.getActive()
          if (!active) {
            deps.redirectToLogin()
          }
        }
      }
    }
    const msg = (err.response?.data as { message?: string } | undefined)?.message || err.message
    if (err.response?.status !== 404) {
      console.error("[API]", msg)
    }
    return Promise.reject(err)
  }

  return {
    authRequestInterceptor,
    authErrorInterceptor,
    resetRefreshLock: () => {
      refreshPromise = null
    },
    hasInFlightRefresh: () => refreshPromise !== null,
  }
}

/** 将拦截器挂到 axios 实例（生产 api-client 使用） */
export function attachAuthInterceptors(
  client: AxiosInstance,
  deps: Omit<AuthInterceptorDeps, "retryRequest"> & {
    retryRequest?: AuthInterceptorDeps["retryRequest"]
  },
): AuthInterceptors {
  const interceptors = createAuthInterceptors({
    ...deps,
    retryRequest: deps.retryRequest ?? ((config) => client(config)),
  })
  client.interceptors.request.use(interceptors.authRequestInterceptor)
  client.interceptors.response.use((r) => r, interceptors.authErrorInterceptor)
  return interceptors
}
