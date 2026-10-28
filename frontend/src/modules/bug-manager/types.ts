/** BUG 单管理 DTO — 与 /api/bugs/* 的 snake_case 契约一致 */

export type BugCategory = "ui_automation" | "case_authoring"
export type BugStatus = "open" | "resolved" | "ignored"

export interface BugSummary {
  total: number
  ui_automation: number
  case_authoring: number
  open: number
  resolved: number
  ignored: number
}

export interface BugTicket {
  id: number
  bug_no: string
  category: BugCategory
  category_label: string
  title: string
  status: BugStatus
  status_label: string
  task_id: number
  task_title: string
  task_kind: string
  task_status: string
  agent_id: number
  created_by: string
  created_at: string
  updated_at: string
  resolved_at: string
  detail?: string
  detail_preview?: string
}

export interface BugListData {
  summary: BugSummary
  total: number
  items: BugTicket[]
  truncated: boolean
}

export interface BugSyncResult {
  scanned: number
  created: number
  updated: number
  skipped: number
}
