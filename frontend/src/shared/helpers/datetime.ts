/**
 * 共享时间格式化（表格展示用）。
 *
 * 本模块的业务功能如下：
 * 1. formatRelativeTime: 把 ISO 时间串转成「刚刚 / N 分钟前 / N 小时前 / 日期」。
 * 2. formatDateTime: 把 ISO 时间串转成「YYYY-MM-DD HH:mm:ss」，供 title 提示绝对时间。
 *
 * 语义与 device-pool/helpers.ts 的既有实现保持一致；那两处旧实现暂未迁回本模块。
 */

/** 空值与非法值的统一兜底 */
const EMPTY_TIME = "—"

/**
 * 相对时间：列表里读起来比 ISO 串快。
 *
 * Args:
 *   iso: 服务端返回的时间串（ISO 8601）。
 *
 * Returns:
 *   刚刚 / N 分钟前 / N 小时前 / 本地日期；空或非法返回「—」。
 */
export function formatRelativeTime(iso: string): string {
  if (!iso) return EMPTY_TIME
  const time = new Date(iso).getTime()
  if (Number.isNaN(time)) return EMPTY_TIME
  // 服务端时钟可能略快于浏览器：负差按「刚刚」处理，避免出现空值与负值文案
  const sec = Math.max(0, Math.floor((Date.now() - time) / 1000))
  if (sec < 60) return "刚刚"
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  return new Date(iso).toLocaleDateString("zh-CN")
}

/**
 * 绝对时间：给 `title` 用，精确到秒。
 *
 * Args:
 *   iso: 服务端返回的时间串（ISO 8601）。
 *
 * Returns:
 *   `YYYY-MM-DD HH:mm:ss`；空或非法返回「—」。
 */
export function formatDateTime(iso: string): string {
  if (!iso) return EMPTY_TIME
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return EMPTY_TIME
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
