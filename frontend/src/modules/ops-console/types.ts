/** 运营后台 · 用户管理：账号行与列表分页 DTO。 */

/** 身份标签：与后端 `identity` 字段一一对应 */
export type OpsIdentity = "superuser" | "operator" | "user"

/** 模型类型：与后端 `model_kind` 字段一一对应 */
export type OpsModelKind = "chat" | "tts" | "realtime"

/** 一行账号 */
export interface OpsUser {
  id: number
  username: string
  email: string
  identity: OpsIdentity
  is_active: boolean
  date_joined: string
  last_login: string
}

/** 分页结果 */
export interface OpsUserPage {
  users: OpsUser[]
  total: number
  page: number
  page_size: number
}

/** 状态筛选：all 不筛，其余映射到 `active` 查询参数 */
export type OpsStatusFilter = "all" | "active" | "inactive"

/** 批量停用的一行结果 */
export interface OpsBatchRow {
  user_id: number
  outcome: "disabled" | "skipped" | "rejected"
  reason: string
}

/** 批量停用响应 */
export interface OpsBatchDisableResult {
  results: OpsBatchRow[]
  counts: { disabled: number; skipped: number; rejected: number }
}

/** 批量注销响应 */
export interface OpsPurgeResult {
  deleted: number[]
}

/** 运营页里的一条 Agent 配置。模型字段来自关联的模型配置。 */
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
}

/** 新建 / 修改入参。模型必须是一条已有模型配置。 */
export interface OpsAgentInput {
  name: string
  model_config_id: number | null
  system_prompt: string
}

/** 一条模型配置。密钥只存环境变量名。 */
export interface OpsModelConfig {
  id: number
  provider: string
  api_protocol: string
  model_kind?: OpsModelKind
  voice?: string
  api_key_env: string
  base_url: string
  model_name: string
}

/** 模型配置入参。 */
export interface OpsModelConfigInput {
  provider: string
  api_protocol: string
  model_kind?: OpsModelKind
  voice?: string
  api_key_env: string
  base_url: string
  model_name: string
}

/** 列表查询参数 */
export interface OpsUserListParams {
  page: number
  page_size: number
  keyword?: string
  active?: "true" | "false"
}
