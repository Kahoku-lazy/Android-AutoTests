/** 单个账号的 token 对（localStorage.auth_accounts 的 value） */
export interface AccountTokens {
  access_token: string
  refresh_token: string
}

/** localStorage.auth_accounts 的完整存储格式 */
export type AuthPool = Record<string, AccountTokens>

/** 登录/注册 API 响应 — discriminated union，if (data.status) 后自动收窄 */
export type AuthResponse =
  | { status: true; access_token: string; refresh_token: string }
  | { status: false; message: string }

/** 登录页视图状态机 */
export type ViewState = 'switchPrompt' | 'login' | 'register'

/** 表单字段校验错误（key 为字段名） */
export interface FieldErrors {
  username?: string
  password?: string
  password2?: string
  email?: string
}
