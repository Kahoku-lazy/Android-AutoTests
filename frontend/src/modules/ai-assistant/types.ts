/** 助手名片与测试对话的页面数据类型。 */

export interface AssistantCard {
  assistant_id: string
  display_name: string
  has_avatar: boolean
  marker: string
  role_id: string
  role_name: string
  tools: ToolSelection[]
}

export interface ToolSelection {
  domain: string
  preset: "all" | "readonly"
  add: string[]
  remove: string[]
}

export interface ToolCatalogDomain {
  domain: string
  label: string
  presets: { id: "all" | "readonly"; label: string }[]
  tools: { name: string; description: string; read_only: boolean }[]
}

export interface SopWorkflow {
  id: number
  name: string
  executor_assistant_id: string
  verifier_assistant_id: string
}

/** 工作流卡片的展示字段：名称、两侧名片显示名与笔色，由 helpers/sop-card.ts 现算。 */
export interface SopWorkflowCard {
  id: number
  name: string
  executor_name: string
  verifier_name: string
  /** 笔色键：取执行助手的 marker，执行助手已不存在时回落 teal */
  marker: string
}

/** 卡片网格里的一张颜料片：助手名片与 SOP 工作流共用同一个组件的两种形体。 */
export type MarkerTile =
  { kind: "assistant"; card: AssistantCard } | { kind: "workflow"; card: SopWorkflowCard }

export interface RoleOption {
  role_id: string
  name: string
}

export interface AssistantThread {
  thread_id: string
  status: string
  title: string
}

export interface ThreadMessage {
  role: "user" | "assistant"
  content: string
  /** 该条消息的本地时间（带偏移的 ISO 8601），页面只取墙上时间 */
  created_at: string
}

/** 该栏的一轮运行日志：编号是时间戳目录名，不是磁盘路径。 */
export interface ThreadLog {
  report_id: string
  summary: string
  /** 该轮助手消息的本地时间（带偏移的 ISO 8601）；进行中的一轮为空串 */
  created_at: string
  writing: boolean
}
