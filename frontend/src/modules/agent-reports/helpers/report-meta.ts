/** 执行报告的纯函数：数值格式化与微倾轮转（无副作用，便于单测） */

import { REPORTS_TILT_STEPS } from "../constants"

const BYTE_UNITS = ["B", "KB", "MB", "GB"] as const
const KILO = 1024
const MINUTE_MS = 60_000
const HOUR_MS = 3_600_000
const DAY_MS = 86_400_000
const PAD_WIDTH = 2

/**
 * 把字节数格式化成一位小数的可读文本。
 *
 * @param bytes 字节数
 * @returns 形如 `33.2 KB`；非法输入返回 `—`
 */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—"
  let value = bytes
  let unitIndex = 0
  while (value >= KILO && unitIndex < BYTE_UNITS.length - 1) {
    value /= KILO
    unitIndex += 1
  }
  const digits = unitIndex === 0 ? 0 : 1
  return `${value.toFixed(digits)} ${BYTE_UNITS[unitIndex]}`
}

/**
 * 把秒级时间戳格式化成相对时间。
 *
 * @param seconds 秒级时间戳
 * @returns 形如 `3 分钟前` / `2 天前`；非法输入返回 `—`
 */
export function formatRunTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return "—"
  const elapsed = Date.now() - seconds * 1000
  if (elapsed < MINUTE_MS) return "刚刚"
  if (elapsed < HOUR_MS) return `${Math.floor(elapsed / MINUTE_MS)} 分钟前`
  if (elapsed < DAY_MS) return `${Math.floor(elapsed / HOUR_MS)} 小时前`
  return `${Math.floor(elapsed / DAY_MS)} 天前`
}

/**
 * 按序号取卡片微倾角度。
 *
 * @param index 卡片在列表中的下标
 * @returns 角度（deg）
 */
export function tiltFor(index: number): number {
  const size = REPORTS_TILT_STEPS.length
  return REPORTS_TILT_STEPS[((index % size) + size) % size]
}

/**
 * 把运行目录名拆成可读的日期时间。
 *
 * @param run 形如 `20261114_200839_ui_executor`
 * @returns 形如 `2026-11-14 20:08:39`；不符合约定时原样返回
 */
export function runStamp(run: string): string {
  const matched = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/.exec(run)
  if (!matched) return run
  const [, year, month, day, hour, minute] = matched
  const second = matched[6]
  const pad = (text: string) => text.padStart(PAD_WIDTH, "0")
  return `${year}-${month}-${day} ${pad(hour)}:${pad(minute)}:${pad(second)}`
}
