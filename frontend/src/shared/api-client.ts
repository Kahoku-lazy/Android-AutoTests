/**
 * 业务接口客户端：请求发往 /api，并带上当前登录凭证。
 *
 * 业务：
 * - 已登录的请求自动带访问凭证
 * - 访问凭证失效时向续期接口换新凭证，再重试刚才的请求
 * - 续期失败则清空会话，整页回到登录页
 */
import axios from "axios"
import { formatApiError } from "@/shared/types/api-error"
import type { AuthResponse } from "@/shared/types/auth"
import { getToken, setToken, clearToken, getRefreshToken } from "@/shared/auth/token-storage"
import { configureTokenRefresh, refreshAccessToken } from "@/shared/auth/token-refresh"
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

// 续期是 HTTP 唯一出口的一部分：把真实请求注入 token-refresh，WS 与拦截器共用
configureTokenRefresh(async (refreshToken) => {
  const response = await axios.post<AuthResponse>("/api/auth/refresh/", {
    refresh_token: refreshToken,
  })
  return response.data
})

attachAuthInterceptors(client, {
  getToken,
  setToken,
  clearToken,
  getRefreshToken,
  // 与 WebSocket 建连共用同一把单飞锁：并发续期只发一次刷新请求
  refreshRequest: async () => {
    const access = await refreshAccessToken()
    return {
      data: { status: true, data: { access_token: access, token_type: "bearer" } } as AuthResponse,
    }
  },
  redirectToLogin: () => {
    window.location.href = "/login"
  },
})

/** 将 axios 错误转为用户可读的中文提示（实现见 shared/types/api-error.ts，此处 re-export 保持既有 import 路径兼容） */
export { formatApiError }

export default client
