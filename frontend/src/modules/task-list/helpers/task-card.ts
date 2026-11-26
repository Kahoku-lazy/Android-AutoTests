export function formatTaskDuration(start?: string, end?: string): string {
  if (!start || !end) return "—"
  const ms = Date.parse(end.replace(" ", "T")) - Date.parse(start.replace(" ", "T"))
  if (!Number.isFinite(ms) || ms < 0) return "—"
  const sec = Math.round(ms / 1000)
  if (sec < 60) return `≈ ${sec}s`
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `≈ ${m}m ${s}s`
}

export function formatTaskCost(cost?: number): string {
  return `${Number(cost ?? 0).toFixed(4)} 元`
}
