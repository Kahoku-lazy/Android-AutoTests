import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios"
import type { ApiError } from "@/shared/types/api-error"
import type { AuthResponse } from "@/shared/types/auth"
import {
  getToken,
  setToken,
  clearToken,
  getRefreshToken,
  getActive,
} from "@/shared/auth/token-storage"

/** 后端统一响应信封 — 所有 Django API 返回此格式 */
export interface DjangoResponse<T = unknown> {
  status: boolean
  data?: T
  message?: string
}

// ── Django API client (business modules) ──
const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 120000, // 2min for LLM API responses
})

// ── Request interceptor — inject JWT ──
function authInterceptor(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

client.interceptors.request.use(authInterceptor)

// ── Response interceptor — handle 401 + token refresh ──
// Deduplication lock: concurrent 401s share a single refresh call so
// the interceptor doesn't cascade into hundreds of retries.
let _refreshPromise: Promise<{ data: AuthResponse }> | null = null

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

async function authErrorInterceptor(
  err: AxiosError,
): Promise<never> {
  const originalRequest = err.config as RetryableRequest | undefined
  if (err.response?.status === 401 && originalRequest && !originalRequest._retry) {
    const currentRefreshToken = getRefreshToken()
    if (currentRefreshToken) {
      originalRequest._retry = true
      try {
        // Reuse an in-flight refresh to prevent N concurrent calls
        if (!_refreshPromise) {
          _refreshPromise = axios
            .post("/api/ai/auth/refresh", {
              refresh_token: currentRefreshToken,
            })
            .finally(() => {
              _refreshPromise = null
            })
        }
        const resp = await _refreshPromise
        if (resp.data.status) {
          setToken(resp.data.access_token)
          originalRequest.headers.Authorization = `Bearer ${resp.data.access_token}`
          return client(originalRequest)
        }
        // refresh returned {status: false} — clear stale promise
        _refreshPromise = null
      } catch {
        _refreshPromise = null
        // refresh failed — remove account; redirect to login only if no accounts left
        clearToken()
        const active = getActive()
        if (!active) {
          window.location.href = "/login"
        }
      }
    }
  }
  const msg = (err.response?.data as { message?: string } | undefined)?.message || err.message
  // 404 通常是"资源不存在"的预期响应，不删屏
  if (err.response?.status !== 404) {
    console.error("[API]", msg)
  }
  return Promise.reject(err)
}

client.interceptors.response.use((r) => r, authErrorInterceptor)

/** 将 axios 错误转为用户可读的中文提示（避免暴露 status code 原文） */
function formatApiError(
  err: ApiError | null | undefined,
  fallback = "操作失败，请稍后重试",
): string {
  const data = err?.response?.data
  if (data && typeof data === "object" && data.message) {
    return data.message
  }
  const body = typeof data === "string" ? data : ""
  if (body.includes("uq_el_element") || body.includes("IntegrityError")) {
    return "该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看或更换目标页面"
  }
  const status = err?.response?.status
  if (status === 409) {
    return "该元素已在当前页面中，请到「元素管理」查看或更换目标页面"
  }
  if (status === 404) return data?.message || "目标不存在，请刷新页面后重试"
  if (status === 401) return "登录已过期，请重新登录"
  if (typeof status === "number" && status >= 500) return "服务暂时异常，请稍后重试"
  if (!err?.response) return "网络连接失败，请确认后端服务已启动"
  if (err.message?.includes("status code")) return fallback
  return err.message || fallback
}

export default client
export { formatApiError }
