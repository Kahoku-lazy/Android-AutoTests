/** 运营后台的常量与文案（用户管理 / 智能体 / 模型配置；唯一真相源）。 */
import type { OpsAgentKind, OpsIdentity, OpsModelKind, OpsStatusFilter } from "./types"

export const OPS_PAGE_TITLE = "用户管理"
export const OPS_PAGE_SUBTITLE = "运营后台：停用 / 启用账号，重置一次性密码；可对本页勾选批量停用"
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

/** 每页固定 10 条：行数选择已下线（与设备 / 任务 / BUG 页同一口径）。 */
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
/** Agent 配置列表每页固定 10 条（与用户管理同口径，翻页键常驻） */
export const OPS_AGENT_PAGE_SIZE = 10
/** Agent 配置的类型：执行者 / 验收者 / 规划者。与后端 `kinds` 取值一一对应。 */
export const OPS_AGENT_KIND_OPTIONS: { value: OpsAgentKind; label: string }[] = [
  { value: "executor", label: "执行者" },
  { value: "verifier", label: "验收者" },
  { value: "planner", label: "规划者" },
]
/** 类型 → 中文名；由 options 派生，避免两处维护同一份文案 */
export const OPS_AGENT_KIND_LABELS = Object.fromEntries(
  OPS_AGENT_KIND_OPTIONS.map((item) => [item.value, item.label]),
) as Record<OpsAgentKind, string>
/** 存量配置还没打类型时的占位文案 */
export const OPS_AGENT_KIND_UNSET = "未分类"
export const OPS_AGENT_COLUMNS = [
  { label: "名称", prop: "name", minWidth: 160 },
  { label: "类型", prop: "kinds", width: 130 },
  { label: "模型配置", prop: "model_name", minWidth: 200 },
  /**
   * 系统提示词是一份几千字的 Markdown：单元格只放一行摘要 + 「查看」，全文交给弹窗。
   * 关掉 EP 溢出 tooltip —— 它会把整段原文塞进一个按内容撑开的深色浮层，超出屏幕即被切掉。
   * 用固定 width 而不是 minWidth：摘要是被裁切的一行，按内容量宽度只会越分越窄。
   */
  { label: "系统提示词", prop: "system_prompt", width: 340, showOverflowTooltip: false },
  { label: "操作", prop: "actions", width: 160, align: "right" },
]
/** 模型配置列表每页固定 10 条（与用户管理 / Agent 配置同口径，翻页键常驻） */
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
/** 新建模型时的默认类型：与后端 `model_kind` 默认值一致。 */
export const OPS_DEFAULT_MODEL_KIND: OpsModelKind = "chat"
export const OPS_MODEL_KIND_OPTIONS: { value: OpsModelKind; label: string }[] = [
  { value: "chat", label: "聊天" },
  { value: "tts", label: "语音合成" },
  { value: "realtime", label: "实时语音" },
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
/** 厂商选项：`kinds` 声明该厂商真实支持的模型类型，页面据此过滤。 */
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
    kinds: ["chat", "realtime", "tts"],
  },
  { value: "openai", label: "openai", key: "OPENAI_API_KEY", kinds: ["chat"] },
]

/**
 * 某个模型类型下真正可选的厂商。
 *
 * Args:
 *   kind: 模型类型；缺省按聊天处理。
 *
 * Returns:
 *   按 `OPS_PROVIDER_OPTIONS` 原顺序过滤后的厂商列表。
 */
export function providersForKind(kind?: string): OpsProviderOption[] {
  const target = kind || OPS_DEFAULT_MODEL_KIND
  return OPS_PROVIDER_OPTIONS.filter((item) => item.kinds.includes(target as OpsModelKind))
}

/**
 * 某个模型类型的默认厂商（列表第一项）。
 *
 * Args:
 *   kind: 模型类型；缺省按聊天处理。
 *
 * Returns:
 *   默认厂商值；该类型没有厂商时返回空串。
 */
export function defaultProviderForKind(kind?: string): string {
  return providersForKind(kind)[0]?.value ?? ""
}

/**
 * 把厂商归一到该模型类型受支持的值：受支持则原样返回，否则回退默认厂商。
 *
 * Args:
 *   kind: 模型类型；缺省按聊天处理。
 *   provider: 待归一的厂商值。
 *
 * Returns:
 *   受支持的厂商值。
 */
export function normalizeProvider(kind?: string, provider?: string): string {
  const allowed = providersForKind(kind)
  return allowed.some((item) => item.value === provider)
    ? (provider as string)
    : defaultProviderForKind(kind)
}

/**
 * 厂商对应的密钥环境变量名。
 *
 * Args:
 *   provider: 厂商值。
 *
 * Returns:
 *   环境变量名；未知厂商返回空串。
 */
export function keyForProvider(provider?: string): string {
  return OPS_PROVIDER_OPTIONS.find((item) => item.value === provider)?.key ?? ""
}

/**
 * 模型类型的中文标签。
 *
 * Args:
 *   kind: 模型类型；缺失或未知按聊天处理。
 *
 * Returns:
 *   中文标签。
 */
export function modelKindLabel(kind?: string): string {
  const matched = OPS_MODEL_KIND_OPTIONS.find(
    (item) => item.value === (kind || OPS_DEFAULT_MODEL_KIND),
  )
  return matched?.label ?? "聊天"
}

export const OPS_GRANT_HINT = "对方将能进入运营后台，查看账号并停用、重置普通用户。"
export const OPS_REVOKE_HINT = "对方将失去运营入口；已打开的页面会在下一次操作时失效。"

/** 身份标签的样式类后缀 */
export function identityClass(identity: OpsIdentity): string {
  return `ops-identity ops-identity--${identity}`
}

/** 模型类型 chip 的类名：缺失或未知类型按聊天处理（与 `modelKindLabel` 同一口径）。 */
export function modelKindClass(kind?: OpsModelKind): string {
  const normalized = kind === "tts" || kind === "realtime" ? kind : "chat"
  return `ops-kind ops-kind--${normalized}`
}
