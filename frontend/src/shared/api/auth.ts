/** Auth API — 登录/注册 HTTP 调用。不从属于任何业务模块，作为认证基础设施独立存在。 */
import djangoClient from '@/shared/api-client'
import type { AuthResponse } from '@/shared/types/auth'

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await djangoClient.post('/ai/auth/login', { username, password })
  return data
}

export async function register(username: string, password: string): Promise<AuthResponse> {
  const { data } = await djangoClient.post('/ai/auth/register', { username, password })
  return data
}
