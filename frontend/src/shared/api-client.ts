import axios from "axios"
import { formatApiError } from "@/shared/types/api-error"
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

/** 将 axios 错误转为用户可读的中文提示（实现见 shared/types/api-error.ts，此处 re-export 保持既有 import 路径兼容） */
export { formatApiError }

export default client
