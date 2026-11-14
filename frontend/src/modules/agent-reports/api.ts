/** 执行报告 API — 平台智能体运行报告（后端 apps/ai_assistant） */
import djangoClient from "@/shared/api-client"

import type { AgentReportContent, AgentReportRow } from "./types"

/** 列表接口的信封 */
export interface AgentReportListResponse {
  status: boolean
  data?: { reports?: AgentReportRow[] }
  message?: string
}

/** 单份报告接口的信封 */
export interface AgentReportDetailResponse {
  status: boolean
  data?: { report?: AgentReportContent }
  message?: string
}

/**
 * 取最近的运行报告。
 *
 * @param limit 最多返回多少条
 * @returns 后端信封，`data` 为报告列表
 */
export async function fetchAgentReports(limit = 50): Promise<AgentReportListResponse> {
  const { data } = await djangoClient.get("/ai/agent-reports/", { params: { limit } })
  return data
}

/**
 * 取一份报告的 HTML 正文。
 *
 * @param run 运行目录名
 * @param name 报告文件名
 * @returns 后端信封，`data.content` 为完整 HTML
 */
export async function fetchAgentReport(
  run: string,
  name: string,
): Promise<AgentReportDetailResponse> {
  const { data } = await djangoClient.get(`/ai/agent-reports/${run}/${name}/`)
  return data
}
