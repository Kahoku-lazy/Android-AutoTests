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

/** 将 axios 错误转为用户可读的中文提示（避免暴露 status code 原文与技术术语） */
export function formatApiError(
  err: ApiError | null | undefined,
  fallback = "操作失败，请稍后重试",
): string {
  const data = err?.response?.data
  if (data && typeof data === "object" && data.message) {
    return data.message
  }
  const body = typeof data === "string" ? data : ""
  if (body.includes("uq_el_element") || body.includes("IntegrityError")) {
    return "该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看或更换目标页面"
  }
  const status = err?.response?.status
  if (status === 409) {
    return "该元素已在当前页面中，请到「元素管理」查看或更换目标页面"
  }
  if (status === 404) return data?.message || "目标不存在，请刷新页面后重试"
  if (status === 401) return "登录已过期，请重新登录"
  if (typeof status === "number" && status >= 500) return "服务暂时异常，请稍后重试"
  if (!err?.response) return "网络连接失败，请稍后重试"
  if (err.message?.includes("status code")) return fallback
  return err.message || fallback
}

/** 从 ApiError 中安全提取用户可读的错误消息（经 formatApiError 净化，不透传技术术语） */
export function getApiErrorMessage(e: unknown, fallback = "服务暂时不可用，请稍后重试"): string {
  if (!isApiError(e)) return fallback
  return formatApiError(e, fallback)
}
