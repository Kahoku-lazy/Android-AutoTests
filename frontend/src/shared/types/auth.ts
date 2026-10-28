/**
 * 认证用到的数据结构：登录结果、登录页处于登录还是注册、表单上的字段错误。
 */

/** 登录/注册成功时带回的会话 */
interface AuthTokenData {
  access_token: string
  refresh_token: string
  token_type?: string
}

/** 续期成功时带回的新访问凭证 */
interface AuthRefreshData {
  access_token: string
  token_type?: string
}

/** 登录、注册、续期、登出的接口结果 */
export interface AuthResponse {
  status?: boolean
  data?: AuthTokenData | AuthRefreshData | Record<string, never>
  message?: string
  retry?: boolean
}

/** 登录页当前是登录还是注册 */
export type ViewState = "login" | "register"

/** 表单字段校验错误（key 为字段名） */
export interface FieldErrors {
  username?: string
  password?: string
  password2?: string
  email?: string
}
