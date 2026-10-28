/**
 * 已登录请求的凭证处理。
 *
 * 业务：
 * - 发出请求时带上当前访问凭证
 * - 访问凭证失效且还有续期凭证时，先续期再重试这一次请求
 * - 续期请求出错时退出登录，回到登录页
 * - 登录、注册、刷新这三处失败不走续期
 */
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios"
import type { AuthResponse } from "@/shared/types/auth"

export interface AuthInterceptorDeps {
  getToken: () => string
  setToken: (token: string) => void
  clearToken: () => void
  getRefreshToken: () => string
  /** 刷新请求（生产用 axios.post，测试可 mock） */
  refreshRequest: (body: { refresh_token: string }) => Promise<{ data: AuthResponse }>
  /** 清空会话后跳转登录页 */
  redirectToLogin: () => void
  /** 用新 token 重试原请求 */
  retryRequest: (config: InternalAxiosRequestConfig) => Promise<unknown>
}

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

/**
 * 登录、注册、刷新。这三处失败表示凭证本身无效，不能当成访问过期去续期，
 * 否则一次密码错误会先换掉本地会话。清单需与网关公开认证路径一致。
 */
export const PUBLIC_AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"] as const

/** 该请求是否指向公开认证端点（兼容相对写法与带 /api 前缀的完整写法）。 */
function isPublicAuthRequest(config: InternalAxiosRequestConfig | undefined): boolean {
  const url = config?.url ?? ""
  return PUBLIC_AUTH_PATHS.some((path) => url.startsWith(path) || url.startsWith("/api" + path))
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
    if (
      err.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isPublicAuthRequest(originalRequest)
    ) {
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
          deps.redirectToLogin()
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
