export interface AssistantCard {
  assistant_id: string
  display_name: string
  has_avatar: boolean
  marker: string
  role_id: string
  role_name: string
  tools: ToolSelection[]
  release_state?: string
  revision?: number
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

export interface WorkflowMember {
  assistant_id: string
  description: string
}

export interface SopWorkflow {
  id: number
  name: string
  orchestration?: "sop" | "goal" | "team"
  kind?: "ui_automation" | "case_authoring" | "requirement_breakdown"
  executor_assistant_id: string
  verifier_assistant_id: string
  leader_assistant_id?: string
  members?: WorkflowMember[]
  release_state?: string
}

export interface SopWorkflowCard {
  id: number
  name: string
  orchestration: "sop" | "goal" | "team"
  kind: "ui_automation" | "case_authoring" | "requirement_breakdown"
  executor_name: string
  verifier_name: string
  leader_name: string
  member_count: number

  marker: string
  release_state?: string
}

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

  created_at: string
}

export interface ThreadLog {
  report_id: string
  summary: string

  created_at: string
  writing: boolean
}
