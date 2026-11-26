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

export async function logout(): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/logout/")
  return data
}

export interface MeUser {
  id: number
  username: string
  is_superuser: boolean
  is_operator: boolean
  is_assistant_author?: boolean
}

export async function me(): Promise<MeUser> {
  const { data } = await djangoClient.get<{ status: boolean; data: { user: MeUser } }>("/auth/me/")
  return data.data.user
}
