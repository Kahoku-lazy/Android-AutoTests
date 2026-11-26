interface AuthTokenData {
  access_token: string
  refresh_token: string
  token_type?: string
}

interface AuthRefreshData {
  access_token: string
  token_type?: string
}

export interface AuthResponse {
  status?: boolean
  data?: AuthTokenData | AuthRefreshData | Record<string, never>
  message?: string
  retry?: boolean
}

export type ViewState = "login" | "register"

export interface FieldErrors {
  username?: string
  password?: string
  password2?: string
  email?: string
}
