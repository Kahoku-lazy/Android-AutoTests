const EMPTY_TIME = "—"

function pad2(value: number): string {
  return String(value).padStart(2, "0")
}

export interface RelativeTimeOptions {
  granularity?: "date" | "long"
}

export interface DateTimeOptions {
  precision?: "minute" | "second"
}

export function formatRelativeTime(iso: string, opts: RelativeTimeOptions = {}): string {
  if (!iso) return EMPTY_TIME
  const time = new Date(iso).getTime()
  if (Number.isNaN(time)) return EMPTY_TIME

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

export function formatDateTime(iso: string, opts: DateTimeOptions = {}): string {
  if (!iso) return EMPTY_TIME
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return EMPTY_TIME
  const head = `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(
    date.getHours(),
  )}:${pad2(date.getMinutes())}`
  return opts.precision === "minute" ? head : `${head}:${pad2(date.getSeconds())}`
}

export function formatMonthDayTime(iso: string): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return `${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(
    date.getMinutes(),
  )}`
}
