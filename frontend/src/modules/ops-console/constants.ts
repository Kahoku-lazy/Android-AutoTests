import type { OpsAgentKind, OpsIdentity, OpsModelKind, OpsStatusFilter } from "./types"

export const OPS_PAGE_TITLE = "用户管理"
export const OPS_PAGE_SUBTITLE = "运营后台：停用 / 启用账号，重置一次性密码；可对本页勾选批量停用"
export const OPS_PAGE_ICON = "users"
export const OPS_PAGE_ICON_GRADIENT =
  "linear-gradient(135deg,var(--c-ops),var(--app-status-danger))"

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

export const OPS_DEFAULT_PAGE_SIZE = 10
export const OPS_KEYWORD_DEBOUNCE_MS = 300

export const OPS_TABLE_COLUMNS = [
  { label: "", prop: "_select", width: 52, align: "center", headerAlign: "center", icon: "☑" },
  {
    label: "账号",
    prop: "user",
    icon: "👤",
    minWidth: 260,
    align: "left",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    label: "身份",
    prop: "identity",
    icon: "🆔",
    width: 130,
    align: "center",
    headerAlign: "center",
  },
  {
    label: "状态",
    prop: "is_active",
    icon: "🔘",
    width: 110,
    align: "center",
    headerAlign: "center",
  },
  {
    label: "注册",
    prop: "date_joined",
    icon: "🕐",
    width: 170,
    align: "center",
    headerAlign: "center",
  },
  {
    label: "最后登录",
    prop: "last_login",
    icon: "🕓",
    width: 170,
    align: "center",
    headerAlign: "center",
  },
  { label: "操作", prop: "actions", icon: "⚙", width: 110, align: "right", headerAlign: "center" },
]

export const OPS_EMPTY_TEXT = {
  noData: "没有符合条件的账号",
  hint: "换个关键字或筛选条件试试",
}

export const OPS_DISABLE_HINT =
  "停用后该账号将无法再登录。对方下一次请求会看到 10 秒退出提示，停用前的登录状态立即作废。"
export const OPS_BATCH_DISABLE_HINT =
  "只停用当前页已勾选、且你能管理的账号。历史记录保留，之后可以再启用。"
export const OPS_PURGE_HINT =
  "只删除账号本身。项目、任务、缺陷仍保留，但不再归属任何账号。不可恢复，对方只能重新注册。"
export const OPS_PURGE_CONFIRM_PREFIX = "注销"
export const OPS_BATCH_OUTCOME_LABELS = {
  disabled: "已停用",
  skipped: "已是停用",
  rejected: "未停用",
} as const
export const OPS_RESET_HINT = "新密码由服务端生成，只在本次显示一次，请立即转告对方。"
export const OPS_AGENT_PAGE_TITLE = "Agent配置"
export const OPS_AGENT_PAGE_SUBTITLE = "只登记名称、一条模型配置和系统提示词"
export const OPS_AGENT_EMPTY = "还没有 Agent 配置"
export const OPS_AGENT_DELETE_HINT = "删除后不可恢复。"

export const OPS_AGENT_PAGE_SIZE = 10

export const OPS_AGENT_KIND_OPTIONS: { value: OpsAgentKind; label: string }[] = [
  { value: "executor", label: "执行者" },
  { value: "verifier", label: "验收者" },
  { value: "planner", label: "规划者" },
]

export const OPS_AGENT_KIND_LABELS = Object.fromEntries(
  OPS_AGENT_KIND_OPTIONS.map((item) => [item.value, item.label]),
) as Record<OpsAgentKind, string>

export const OPS_AGENT_KIND_UNSET = "未分类"
export const OPS_AGENT_COLUMNS = [
  { label: "名称", prop: "name", minWidth: 160 },
  { label: "类型", prop: "kinds", width: 130 },
  { label: "模型配置", prop: "model_name", minWidth: 200 },

  { label: "系统提示词", prop: "system_prompt", width: 340, showOverflowTooltip: false },
  { label: "操作", prop: "actions", width: 160, align: "right" },
]

export const OPS_MODEL_PAGE_SIZE = 10
export const OPS_MODEL_COLUMNS = [
  {
    label: "模型",
    prop: "model",
    icon: "◇",
    minWidth: 260,
    align: "left",
    headerAlign: "center",
    showOverflowTooltip: false,
  },
  {
    label: "类型",
    prop: "model_kind",
    icon: "🏷",
    width: 140,
    align: "center",
    headerAlign: "center",
  },
  {
    label: "密钥环境变量",
    prop: "api_key_env",
    icon: "🔑",
    minWidth: 190,
    align: "center",
    headerAlign: "center",
  },
  {
    label: "地址",
    prop: "base_url",
    icon: "🌐",
    minWidth: 220,
    align: "center",
    headerAlign: "center",
  },
  { label: "操作", prop: "actions", icon: "⚙", width: 150, align: "right", headerAlign: "center" },
]

export const OPS_DEFAULT_MODEL_KIND: OpsModelKind = "chat"
export const OPS_MODEL_KIND_OPTIONS: { value: OpsModelKind; label: string }[] = [
  { value: "chat", label: "聊天" },
  { value: "tts", label: "语音合成" },
  { value: "realtime", label: "实时语音" },
  { value: "embedding", label: "向量" },
]
export const OPS_TTS_VOICES = ["Cherry", "Serena", "Ethan", "Chelsie"]
export const OPS_OMNI_VOICES = [
  "Tina",
  "Cindy",
  "Liora Mira",
  "Raymond",
  "Zane",
  "Katerina",
  "Ryan",
  "Mia",
  "Cici",
  "Theo Calm",
  "Serena",
  "Maia",
  "Evan",
  "Qiao",
  "Momo",
  "Wil",
  "Angel",
  "Li Cassian",
  "Joyner",
  "Gold",
  "Jennifer",
  "Aiden",
  "Mione",
  "Sunny",
  "Dylan",
  "Eric",
  "Peter",
  "Joseph Chen",
  "Marcus",
  "Li",
  "Rocky",
  "Kiki",
  "Sohee",
  "Eliška",
  "Alek",
  "Arda",
  "Dolce",
  "Lenn",
  "Ono Anna",
  "Sonrisa",
  "Bodega",
  "Emilien",
  "Andre",
  "Radio Gol",
  "Rizky",
  "Roya",
  "Hana",
  "Jakub",
  "Griet",
  "Marina",
  "Siiri",
  "Ingrid",
  "Sigga",
  "Bea",
  "Chloe",
  "Cherry",
  "Nofish",
  "Jada",
]
export const OPS_PROTOCOL_OPTIONS = [
  { value: "deepseek", label: "DeepSeek" },
  { value: "dashscope", label: "DashScope" },
  { value: "openai", label: "OpenAI 兼容" },
]

export interface OpsProviderOption {
  value: string
  label: string
  key: string
  kinds: OpsModelKind[]
}
export const OPS_PROVIDER_OPTIONS: OpsProviderOption[] = [
  { value: "deepseek", label: "deepseek", key: "DEEPSEEK_API_KEY", kinds: ["chat"] },
  {
    value: "dashscope",
    label: "dashscope",
    key: "DASHSCOPE_API_KEY",
    kinds: ["chat", "realtime", "tts", "embedding"],
  },
  { value: "openai", label: "openai", key: "OPENAI_API_KEY", kinds: ["chat"] },
]

export function providersForKind(kind?: string): OpsProviderOption[] {
  const target = kind || OPS_DEFAULT_MODEL_KIND
  return OPS_PROVIDER_OPTIONS.filter((item) => item.kinds.includes(target as OpsModelKind))
}

export function defaultProviderForKind(kind?: string): string {
  return providersForKind(kind)[0]?.value ?? ""
}

export function normalizeProvider(kind?: string, provider?: string): string {
  const allowed = providersForKind(kind)
  return allowed.some((item) => item.value === provider)
    ? (provider as string)
    : defaultProviderForKind(kind)
}

export function keyForProvider(provider?: string): string {
  return OPS_PROVIDER_OPTIONS.find((item) => item.value === provider)?.key ?? ""
}

export function modelKindLabel(kind?: string): string {
  const matched = OPS_MODEL_KIND_OPTIONS.find(
    (item) => item.value === (kind || OPS_DEFAULT_MODEL_KIND),
  )
  return matched?.label ?? "聊天"
}

export const OPS_GRANT_HINT = "对方将能进入运营后台，查看账号并停用、重置普通用户。"
export const OPS_REVOKE_HINT = "对方将失去运营入口；已打开的页面会在下一次操作时失效。"

export function identityClass(identity: OpsIdentity): string {
  return `ops-identity ops-identity--${identity}`
}

export function modelKindClass(kind?: OpsModelKind): string {
  const normalized = kind === "tts" || kind === "realtime" || kind === "embedding" ? kind : "chat"
  return `ops-kind ops-kind--${normalized}`
}
