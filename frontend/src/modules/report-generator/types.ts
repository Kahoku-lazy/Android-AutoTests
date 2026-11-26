export type ReportSource = "sop" | "agent"

export interface SopReportRow {
  source: "sop"
  report_run: string
  report_name: string
  task_id: number
  task_title: string
  case_label: string
  device: string
  status: string
  started_at: string
  finished_at: string
  duration: string
}

export interface AgentReportRow {
  source: "agent"
  assistant_id: string
  assistant_name: string
  thread_id: string
  report_id: string
  summary: string
  created_at: string
}

export type ReportRow = SopReportRow | AgentReportRow

export interface ReportSummary {
  total_reports: number
  sop_reports: number
  agent_reports: number
}

export interface ReportListData {
  summary: ReportSummary
  total: number
  items: ReportRow[]
}
