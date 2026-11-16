/** 运营后台 · 用户管理：账号行与列表分页 DTO。 */

/** 身份标签：与后端 `identity` 字段一一对应 */
export type OpsIdentity = "superuser" | "operator" | "user"

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

/** 列表查询参数 */
export interface OpsUserListParams {
  page: number
  page_size: number
  keyword?: string
  active?: "true" | "false"
}
