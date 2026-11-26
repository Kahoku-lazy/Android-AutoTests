const CLOCK_RE = /T(\d{2}):(\d{2})/
const DAY_CLOCK_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/
const REPORT_ID_RE = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/

export function clockLabel(iso: string): string {
  const match = CLOCK_RE.exec(iso || "")
  return match ? `${match[1]}:${match[2]}` : ""
}

export function dayClockLabel(iso: string): string {
  const match = DAY_CLOCK_RE.exec(iso || "")
  return match ? `${match[2]}-${match[3]} ${match[4]}:${match[5]}` : ""
}

export function threadLogTime(reportId: string): string {
  const match = REPORT_ID_RE.exec(reportId)
  if (!match) return reportId
  const [, , month, day, hour, minute] = match
  return `${month}-${day} ${hour}:${minute}`
}

export function logCardTime(createdAt: string, reportId: string): string {
  return dayClockLabel(createdAt) || threadLogTime(reportId)
}
