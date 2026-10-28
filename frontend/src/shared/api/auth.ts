/**
 * 认证接口：登录、注册、登出，以及读取当前用户。
 *
 * 业务：
 * - 登录、注册：提交账号凭证，成功时带回本次会话
 * - 登出：使当前登录失效
 * - 当前用户：读取身份，含是否管理员
 */
import djangoClient from "@/shared/api-client"
import type { AuthResponse } from "@/shared/types/auth"

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/login/", { username, password })
  return data
}

export async function register(
  username: string,
  password: string,
  password2: string,
  email: string,
): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/register/", {
    username,
    password,
    password2,
    email,
  })
  return data
}

/** 登出：使当前登录失效。需已登录。 */
export async function logout(): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/logout/")
  return data
}

/** 当前登录用户，含是否管理员。 */
export interface MeUser {
  id: number
  username: string
  is_superuser: boolean
}

export async function me(): Promise<MeUser> {
  const { data } = await djangoClient.get<{ status: boolean; data: { user: MeUser } }>("/auth/me/")
  return data.data.user
}
