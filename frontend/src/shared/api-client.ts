import axios from "axios"
import type { ApiError } from "@/shared/types/api-error"
import {
  getToken,
  setToken,
  clearToken,
  getRefreshToken,
  getActive,
} from "@/shared/auth/token-storage"
import { attachAuthInterceptors } from "@/shared/api-auth-interceptors"

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

attachAuthInterceptors(client, {
  getToken,
  setToken,
  clearToken,
  getRefreshToken,
  getActive,
  refreshRequest: (body) => axios.post("/api/auth/refresh", body),
  redirectToLogin: () => {
    window.location.href = "/login"
  },
})

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
  if (!err?.response) return "网络连接失败，请稍后重试"
  if (err.message?.includes("status code")) return fallback
  return err.message || fallback
}

export default client
export { formatApiError }
