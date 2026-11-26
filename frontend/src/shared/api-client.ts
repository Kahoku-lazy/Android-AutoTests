import axios from "axios"
import { formatApiError } from "@/shared/types/api-error"
import type { AuthResponse } from "@/shared/types/auth"
import { getToken, setToken, clearToken, getRefreshToken } from "@/shared/auth/token-storage"
import { configureTokenRefresh, refreshAccessToken } from "@/shared/auth/token-refresh"
import { attachAuthInterceptors } from "@/shared/api-auth-interceptors"

export interface DjangoResponse<T = unknown> {
  status: boolean
  data?: T
  message?: string
}

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 120000,
})

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

export { formatApiError }

export default client
