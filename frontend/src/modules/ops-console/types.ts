export type OpsIdentity = "superuser" | "operator" | "user"

export type OpsModelKind = "chat" | "tts" | "realtime" | "embedding"

export interface OpsUser {
  id: number
  username: string
  email: string
  identity: OpsIdentity
  is_active: boolean
  date_joined: string
  last_login: string
}

export interface OpsUserPage {
  users: OpsUser[]
  total: number
  page: number
  page_size: number
}

export type OpsStatusFilter = "all" | "active" | "inactive"

export interface OpsBatchRow {
  user_id: number
  outcome: "disabled" | "skipped" | "rejected"
  reason: string
}

export interface OpsBatchDisableResult {
  results: OpsBatchRow[]
  counts: { disabled: number; skipped: number; rejected: number }
}

export interface OpsPurgeResult {
  deleted: number[]
}

export type OpsAgentKind = "executor" | "verifier" | "planner"

export interface OpsAgent {
  role_id: string
  name: string
  model_config_id: number
  provider: string
  api_key_env: string
  model_name: string
  base_url: string
  api_protocol: string
  system_prompt: string

  kinds: OpsAgentKind[]
  created_at?: string
  updated_at?: string
}

export interface OpsAgentInput {
  name: string
  model_config_id: number | null
  system_prompt: string
  kinds: OpsAgentKind[]
}

export interface OpsModelConfig {
  id: number
  provider: string
  api_protocol: string
  model_kind?: OpsModelKind
  voice?: string
  dimensions?: number | null
  api_key_env: string
  base_url: string
  model_name: string
}

export interface OpsModelConfigInput {
  provider: string
  api_protocol: string
  model_kind?: OpsModelKind
  voice?: string
  dimensions?: number | null
  api_key_env: string
  base_url: string
  model_name: string
}

export interface OpsUserListParams {
  page: number
  page_size: number
  keyword?: string
  active?: "true" | "false"
}
