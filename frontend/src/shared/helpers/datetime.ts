const EMPTY_TIME = "—"

export function formatRelativeTime(iso: string): string {
  if (!iso) return EMPTY_TIME
  const time = new Date(iso).getTime()
  if (Number.isNaN(time)) return EMPTY_TIME

  const sec = Math.max(0, Math.floor((Date.now() - time) / 1000))
  if (sec < 60) return "刚刚"
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  return new Date(iso).toLocaleDateString("zh-CN")
}

export function formatDateTime(iso: string): string {
  if (!iso) return EMPTY_TIME
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return EMPTY_TIME
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
