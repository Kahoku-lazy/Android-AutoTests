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

export function formatTaskCreator(name?: string): string {
  const text = (name || "").trim()
  return text || "—"
}

const CREATOR_PENS = [
  "var(--c-dashboard)",
  "var(--c-device)",
  "var(--c-element)",
  "var(--c-case)",
  "var(--c-runner)",
  "var(--c-report)",
  "var(--c-ai)",
  "var(--c-workflow)",
  "var(--c-ops)",
]

function creatorHash(name: string): number {
  let hash = 0x811c9dc5
  for (const byte of new TextEncoder().encode(name)) {
    hash ^= byte
    hash = Math.imul(hash, 0x01000193) >>> 0
  }
  return hash
}

export function creatorPenVars(name?: string): Record<string, string> {
  const text = (name || "").trim()
  if (!text) return {}
  const pen = CREATOR_PENS[creatorHash(text.toLowerCase()) % CREATOR_PENS.length]
  return { "--cp-color": pen }
}
