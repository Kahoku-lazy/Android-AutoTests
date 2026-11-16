/** 运营后台 · 用户管理的常量与文案（唯一真相源）。 */
import type { OpsIdentity, OpsStatusFilter } from "./types"

export const OPS_PAGE_TITLE = "用户管理"
export const OPS_PAGE_SUBTITLE = "运营后台：停用 / 启用账号，重置一次性密码"
export const OPS_PAGE_ICON = "users"
export const OPS_PAGE_ICON_GRADIENT =
  "linear-gradient(135deg,var(--c-ops),var(--app-status-danger))"

/** 状态筛选页签：key 直接对应 composable 的筛选状态 */
export const OPS_FILTER_TABS: { key: OpsStatusFilter; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "active", label: "启用" },
  { key: "inactive", label: "停用" },
]

export const OPS_KEYWORD_PLACEHOLDER = "搜索账号或邮箱"

export const OPS_IDENTITY_LABELS: Record<OpsIdentity, string> = {
  superuser: "超级管理员",
  operator: "运营",
  user: "普通用户",
}

export const OPS_PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
export const OPS_DEFAULT_PAGE_SIZE = 20
export const OPS_KEYWORD_DEBOUNCE_MS = 300

export const OPS_TABLE_COLUMNS = [
  { label: "账号", prop: "username", width: 150 },
  { label: "邮箱", prop: "email", minWidth: 180 },
  { label: "身份", prop: "identity", width: 120 },
  { label: "状态", prop: "is_active", width: 100 },
  { label: "注册时间", prop: "date_joined", width: 150 },
  { label: "最后登录", prop: "last_login", width: 150 },
  { label: "操作", prop: "actions", width: 100, align: "right" },
]

export const OPS_EMPTY_TEXT = {
  noData: "没有符合条件的账号",
  hint: "换个关键字或筛选条件试试",
}

export const OPS_DISABLE_HINT = "停用后该账号将无法再登录；已签发的登录状态最长 1 小时内仍有效。"
export const OPS_RESET_HINT = "新密码由服务端生成，只在本次显示一次，请立即转告对方。"
export const OPS_GRANT_HINT = "对方将能进入运营后台，查看账号并停用、重置普通用户。"
export const OPS_REVOKE_HINT = "对方将失去运营入口；已打开的页面会在下一次操作时失效。"

/** 身份标签的样式类后缀 */
export function identityClass(identity: OpsIdentity): string {
  return `ops-identity ops-identity--${identity}`
}
