/** 报告行的展示派生 — 纯函数，无状态无副作用 */
import type { ReportRow } from "../types"

/** 行唯一键：来源 + 报告定位，两来源合表不撞键。 */
export function reportRowKey(row: ReportRow): string {
  return row.source === "sop"
    ? `sop:${row.report_run}:${row.report_name}`
    : `agent:${row.thread_id}:${row.report_id}`
}

/** 身份列主标题：SOP 行是用例名称（缺省回落任务标题），智能体行是助手名称。 */
export function identityTitle(row: ReportRow): string {
  if (row.source === "sop") return row.case_label || row.task_title || "—"
  return row.assistant_name || row.assistant_id || "—"
}

/** 身份列副行：SOP 行是任务标题，智能体行是助手编号。 */
export function identitySub(row: ReportRow): string {
  return row.source === "sop" ? row.task_title : row.assistant_id
}

/** 关联列：SOP 行是任务编号，智能体行是对话栏编号。 */
export function relationLabel(row: ReportRow): string {
  return row.source === "sop" ? `#${row.task_id}` : row.thread_id
}

/** 结果摘要列：SOP 行给设备与耗时，智能体行给一句话结果。 */
export function outcomeText(row: ReportRow): string {
  if (row.source === "sop") {
    return [row.device, row.duration].filter((part) => part && part !== "—").join(" · ")
  }
  return row.summary || "—"
}

/** 生成时间：SOP 行取结束时间，智能体行取消息时间。 */
export function reportMoment(row: ReportRow): string {
  return row.source === "sop" ? row.finished_at || row.started_at : row.created_at
}

/** 本地时间展示：月-日 时:分；空值给「—」。 */
export function formatReportTime(iso: string): string {
  if (!iso) return "—"
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes(),
  )}`
}
