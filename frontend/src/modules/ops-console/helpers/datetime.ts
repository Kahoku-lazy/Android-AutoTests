/**
 * 运营台表格的时间格式化 — 薄包装，唯一实现见 `@/shared/helpers/datetime`。
 *
 * 本模块的业务功能如下：
 * 1. formatRelativeTime: 相对时间；运营台要「天 / 月 / 年」三档，故固定 `granularity: "long"`。
 * 2. formatDateTime: 绝对时间作为相对时间的副行，只到分（`precision: "minute"`）。
 *
 * 保留本文件是为了让页面侧 import 与断言口径不变（见设计 D9）；不要在别处再写一份实现。
 */
import {
  formatDateTime as formatDateTimeShared,
  formatRelativeTime as formatRelativeTimeShared,
} from "@/shared/helpers/datetime"

/**
 * 相对时间的口语写法（含天 / 月 / 年）。
 *
 * Args:
 *   value: 后端返回的时间字符串（ISO 或 `YYYY-MM-DD HH:mm`），可为空。
 *
 * Returns:
 *   「刚刚」/「N 分钟前」/「N 小时前」/「N 天前」/「N 个月前」/「N 年前」；空或非法返回 `—`。
 */
export function formatRelativeTime(value: string): string {
  return formatRelativeTimeShared(value, { granularity: "long" })
}

/**
 * 绝对时间：`YYYY-MM-DD HH:mm`。
 *
 * Args:
 *   value: 后端返回的时间字符串，可为空。
 *
 * Returns:
 *   格式化后的本地时间；空或非法返回 `—`。
 */
export function formatDateTime(value: string): string {
  return formatDateTimeShared(value, { precision: "minute" })
}
