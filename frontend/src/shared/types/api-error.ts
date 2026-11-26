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

export function isApiError(e: unknown): e is ApiError {
  return typeof e === "object" && e !== null
}

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

export function getApiErrorMessage(e: unknown, fallback = "服务暂时不可用，请稍后重试"): string {
  if (!isApiError(e)) return fallback
  return formatApiError(e, fallback)
}
