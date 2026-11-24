/**
 * 前端时间格式化的**唯一实现**（表格与卡片展示用）。
 *
 * 本模块的业务功能如下：
 * 1. formatRelativeTime: 相对时间「刚刚 / N 分钟前 / N 小时前 / 日期」。
 *    - 默认（`granularity: "date"`）：超过一天回落本地日期 —— 设备池、用例表口径。
 *    - `granularity: "long"`：超过一天改走「N 天前 / N 个月前 / N 年前」—— 运营台口径。
 * 2. formatDateTime: 绝对时间 `YYYY-MM-DD HH:mm:ss`（默认）或 `YYYY-MM-DD HH:mm`（`precision: "minute"`）。
 * 3. formatMonthDayTime: `MM-DD HH:mm` —— 报告台账口径；无法解析返回 null，由调用方决定兜底。
 * 4. formatIsoNaive: 不解析 Date、不做时区换算，只把 `T` 换空格并截到分 —— 任务卡口径。
 *
 * 各调用方的输出口径由 `tests/**\/datetime.spec.ts` 的快照用例锁住；改档位前先改用例。
 */

/** 空值与非法值的统一兜底 */
const EMPTY_TIME = "—"

/** 两位补零：月 / 日 / 时 / 分 / 秒共用 */
function pad2(value: number): string {
  return String(value).padStart(2, "0")
}

export interface RelativeTimeOptions {
  /**
   * 超过一天后的档位：
   * - `date`（默认）：回落本地日期，如 `2026/11/21`；
   * - `long`：`N 天前 / N 个月前 / N 年前`。
   */
  granularity?: "date" | "long"
}

export interface DateTimeOptions {
  /**
   * 精度：
   * - `second`（默认）：`YYYY-MM-DD HH:mm:ss`；
   * - `minute`：`YYYY-MM-DD HH:mm`。
   */
  precision?: "minute" | "second"
}

/**
 * 相对时间：列表里读起来比 ISO 串快。
 *
 * Args:
 *   iso: 服务端返回的时间串（ISO 8601）。
 *   opts: 超过一天后的档位，默认回落本地日期。
 *
 * Returns:
 *   刚刚 / N 分钟前 / N 小时前 / 日期（或天月年）；空或非法返回「—」。
 */
export function formatRelativeTime(iso: string, opts: RelativeTimeOptions = {}): string {
  if (!iso) return EMPTY_TIME
  const time = new Date(iso).getTime()
  if (Number.isNaN(time)) return EMPTY_TIME
  // 服务端时钟可能略快于浏览器：负差按「刚刚」处理，避免出现空值与负值文案
  const sec = Math.max(0, Math.floor((Date.now() - time) / 1000))
  if (sec < 60) return "刚刚"
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  if (opts.granularity === "long") {
    const days = Math.floor(sec / 86400)
    if (days < 30) return `${days} 天前`
    const months = Math.floor(days / 30)
    if (months < 12) return `${months} 个月前`
    return `${Math.floor(days / 365)} 年前`
  }
  return new Date(iso).toLocaleDateString("zh-CN")
}

/**
 * 绝对时间：给 `title` 与表格主/副行用。
 *
 * Args:
 *   iso: 服务端返回的时间串（ISO 8601）。
 *   opts: 精度，默认到秒。
 *
 * Returns:
 *   `YYYY-MM-DD HH:mm:ss`（或到分）；空或非法返回「—」。
 */
export function formatDateTime(iso: string, opts: DateTimeOptions = {}): string {
  if (!iso) return EMPTY_TIME
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return EMPTY_TIME
  const head = `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(
    date.getHours(),
  )}:${pad2(date.getMinutes())}`
  return opts.precision === "minute" ? head : `${head}:${pad2(date.getSeconds())}`
}

/**
 * 「月-日 时:分」：报告台账的时间列。
 *
 * Args:
 *   iso: 服务端返回的时间串。
 *
 * Returns:
 *   `MM-DD HH:mm`；无法解析返回 `null`（调用方按各自口径兜底：台账原样返回、BUG 单给「—」）。
 */
export function formatMonthDayTime(iso: string): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return `${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(
    date.getMinutes(),
  )}`
}

/**
 * 原样呈现服务端墙钟时间：**不解析 Date、不做时区换算**。
 *
 * 平台单时区；经 `new Date()` 解析会按浏览器时区换算，跨时区访问时会显示错。
 *
 * Args:
 *   raw: 服务端返回的时间串，形如 `2026-11-24T12:34:56` 或 `2026-11-24 12:34:56`。
 *
 * Returns:
 *   `YYYY-MM-DD HH:mm`；空值返回空串。
 */
export function formatIsoNaive(raw?: string): string {
  if (!raw) return ""
  return raw.replace("T", " ").slice(0, 16)
}
