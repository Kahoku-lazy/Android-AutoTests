/** 执行报告模块 DTO — 与 GET /api/ai/agent-reports/ 的返回字段一一对应 */

/** 一条平台运行报告（后端由报告目录整理而来） */
export interface AgentReportRow {
  /** 运行目录名，形如 20261114_200839_ui_executor */
  run: string
  /** 报告文件名；没有 HTML 时为空串 */
  report: string
  /** 日志文件名 */
  log: string
  /** 报告字节数 */
  bytes: number
  /** 报告修改时间（秒级时间戳） */
  modified_at: number
}

/** 报告正文 */
export interface AgentReportContent {
  run: string
  name: string
  content: string
}
