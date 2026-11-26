import { formatMonthDayTime } from "@/shared/helpers/datetime"
import type { ReportRow } from "../types"

export function reportRowKey(row: ReportRow): string {
  return row.source === "sop"
    ? `sop:${row.report_run}:${row.report_name}`
    : `agent:${row.thread_id}:${row.report_id}`
}

export function identityTitle(row: ReportRow): string {
  if (row.source === "sop") return row.case_label || row.task_title || "—"
  return row.assistant_name || row.assistant_id || "—"
}

export function identitySub(row: ReportRow): string {
  return row.source === "sop" ? row.task_title : row.assistant_id
}

export function relationLabel(row: ReportRow): string {
  return row.source === "sop" ? `#${row.task_id}` : row.thread_id
}

export function outcomeText(row: ReportRow): string {
  if (row.source === "sop") {
    return [row.device, row.duration].filter((part) => part && part !== "—").join(" · ")
  }
  return row.summary || "—"
}

export function reportMoment(row: ReportRow): string {
  return row.source === "sop" ? row.finished_at || row.started_at : row.created_at
}

export function formatReportTime(iso: string): string {
  if (!iso) return "—"
  return formatMonthDayTime(iso) ?? iso
}
