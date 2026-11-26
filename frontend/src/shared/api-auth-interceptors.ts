import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios"
import type { AuthResponse } from "@/shared/types/auth"
import { isAccountDisabled, startAccountDisabledCountdown } from "@/shared/auth/account-disabled"

export interface AuthInterceptorDeps {
  getToken: () => string
  setToken: (token: string) => void
  clearToken: () => void
  getRefreshToken: () => string

  refreshRequest: (body: { refresh_token: string }) => Promise<{ data: AuthResponse }>

  redirectToLogin: () => void

  retryRequest: (config: InternalAxiosRequestConfig) => Promise<unknown>
}

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

export const PUBLIC_AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"] as const

function isPublicAuthRequest(config: InternalAxiosRequestConfig | undefined): boolean {
  const url = config?.url ?? ""
  return PUBLIC_AUTH_PATHS.some((path) => url.startsWith(path) || url.startsWith("/api" + path))
}

export interface AuthInterceptors {
  authRequestInterceptor: (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig
  authErrorInterceptor: (err: AxiosError) => Promise<unknown>

  resetRefreshLock: () => void

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
    if (isAccountDisabled(err.response?.data)) {
      startAccountDisabledCountdown(deps.clearToken, deps.redirectToLogin)
      return Promise.reject(err)
    }
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
