/**
 * 对话页的时间标签。
 *
 * 后端给的是带偏移的本地时间 ISO（如 `2026-11-16T17:55:30+08:00`）。这里只取
 * 墙上时间、不做时区换算——平台单时区，换算只会在浏览器时区不同时显示错。
 * 日志编号（`YYYYMMDD_HHMMSS`）只在老数据缺 `created_at` 时做回落。
 */

const CLOCK_RE = /T(\d{2}):(\d{2})/
const DAY_CLOCK_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/
const REPORT_ID_RE = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/

/** 气泡时刻：`HH:mm`。 */
export function clockLabel(iso: string): string {
  const match = CLOCK_RE.exec(iso || "")
  return match ? `${match[1]}:${match[2]}` : ""
}

/** 跨日场景的日期时刻：`MM-DD HH:mm`。 */
export function dayClockLabel(iso: string): string {
  const match = DAY_CLOCK_RE.exec(iso || "")
  return match ? `${match[2]}-${match[3]} ${match[4]}:${match[5]}` : ""
}

/** 报告编号里的时间戳 → `MM-DD HH:mm`；形态不符时原样返回。 */
export function threadLogTime(reportId: string): string {
  const match = REPORT_ID_RE.exec(reportId)
  if (!match) return reportId
  const [, , month, day, hour, minute] = match
  return `${month}-${day} ${hour}:${minute}`
}

/** 日志卡时间：优先该轮消息时间，老数据回落报告编号。 */
export function logCardTime(createdAt: string, reportId: string): string {
  return dayClockLabel(createdAt) || threadLogTime(reportId)
}
