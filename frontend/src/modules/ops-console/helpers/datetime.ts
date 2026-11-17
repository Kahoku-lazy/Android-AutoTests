/**
 * 运营表格的时间格式化 — 纯函数，两个列表页共用。
 *
 * 业务功能：
 * 1. formatRelativeTime: 把时间点转成「刚刚 / N 分钟前 / N 小时前 / 日期」。
 * 2. formatDateTime: 把时间点转成 `YYYY-MM-DD HH:mm`，作为相对时间的副行。
 */

/** 空值与非法时间统一显示为占位符，避免表格里出现 `Invalid Date`。 */
const EMPTY = "—"

/**
 * 相对时间的口语写法。
 *
 * Args:
 *   value: 后端返回的时间字符串（ISO 或 `YYYY-MM-DD HH:mm`），可为空。
 *
 * Returns:
 *   「刚刚」/「N 分钟前」/「N 小时前」/「YYYY/M/D」；空或非法时间返回 `—`。
 */
export function formatRelativeTime(value: string): string {
  if (!value) return EMPTY
  const time = new Date(value).getTime()
  if (Number.isNaN(time)) return EMPTY
  const seconds = Math.floor((Date.now() - time) / 1000)
  if (seconds < 60) return "刚刚"
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`
  const days = Math.floor(seconds / 86400)
  if (days < 30) return `${days} 天前`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months} 个月前`
  return `${Math.floor(days / 365)} 年前`
}

/**
 * 绝对时间：`YYYY-MM-DD HH:mm`。
 *
 * Args:
 *   value: 后端返回的时间字符串，可为空。
 *
 * Returns:
 *   格式化后的本地时间；空或非法时间返回 `—`。
 */
export function formatDateTime(value: string): string {
  if (!value) return EMPTY
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return EMPTY
  const pad = (n: number): string => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
