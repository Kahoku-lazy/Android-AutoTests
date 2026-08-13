/** API 错误类型 — 用于 catch 块中安全地提取错误信息，替代 `catch (e: any)`。 */

/** axios 错误响应中可能包含的后端错误信息 */
export interface ApiError {
  response?: {
    status?: number
    data?: {
      status?: boolean
      message?: string
    }
  }
  message?: string
}

/** 类型守卫：判断一个 unknown 值是否符合 ApiError 结构 */
export function isApiError(e: unknown): e is ApiError {
  return typeof e === "object" && e !== null
}

/** 从 ApiError 中安全提取用户可读的错误消息 */
export function getApiErrorMessage(e: unknown, fallback = "服务暂时不可用，请稍后重试"): string {
  if (!isApiError(e)) return fallback
  return e.response?.data?.message || fallback
}
