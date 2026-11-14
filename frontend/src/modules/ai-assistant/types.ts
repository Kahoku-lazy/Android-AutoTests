/** AI 助手模块 DTO：编排卡片。模型不对外。 */

export interface WorkflowCard {
  key: string
  name: string
  summary: string
  /** 上线日期（YYYY-MM-DD）；没有时为空 */
  released_at?: string
}

export interface WorkflowListResponse {
  status: boolean
  data?: { workflows?: WorkflowCard[] }
  message?: string
}
