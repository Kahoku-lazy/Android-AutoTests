/** 测试报告台账 DTO — 与 GET /api/reports/ 的 snake_case 契约一致 */

export type ReportSource = "sop" | "agent"

/** SOP 报告行：终态任务 + 报告定位 + 冻结用例身份 */
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

/** 智能体报告行：正常完成的助手对话轮次 */
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

/** 报告数量统计（不是任务通过率） */
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
