/** 登录/注册成功时 data 载荷 */
interface AuthTokenData {
  access_token: string
  refresh_token: string
  token_type?: string
}

/** refresh 成功时 data 载荷 */
interface AuthRefreshData {
  access_token: string
  token_type?: string
}

/** 登录/注册/refresh/logout API 响应 — 信封格式 */
export interface AuthResponse {
  status?: boolean
  data?: AuthTokenData | AuthRefreshData | Record<string, never>
  message?: string
  retry?: boolean
}

/** 登录页视图状态机 */
export type ViewState = "login" | "register"

/** 表单字段校验错误（key 为字段名） */
export interface FieldErrors {
  username?: string
  password?: string
  password2?: string
  email?: string
}
