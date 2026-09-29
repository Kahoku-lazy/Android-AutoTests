/** Toolbox + MCP + Skills API — TypeScript */
import djangoClient from "@/shared/api-client"
import type {
  ToolboxListResponse,
  AgentOpResponse,
  ModelDebugLogBasis,
  TaskLogCheck,
  TaskLogEvidence,
} from "@/shared/types/ai"

// ── 共享工具箱项 DTO（类型跟着实现走，消费方从此处 import） ──
export interface SharedToolItem {
  id: number
  name: string
  item_type: string
  description?: string
  config_json?: string
  enabled: boolean
  created_at?: string
  origin?: "local" | "uploaded"
  missing?: boolean
}

export interface SkillTreeNode {
  name: string
  path: string
  is_dir: boolean
  children?: SkillTreeNode[]
}

export interface SkillFilePayload {
  path: string
  name: string
  kind: "markdown" | "text" | "unsupported" | "too_large"
  content: string
}

// ── Toolbox (shared tools / skills / extensions) ──

export async function fetchSharedTools(): Promise<ToolboxListResponse> {
  const { data } = await djangoClient.get<ToolboxListResponse>("/ai/toolbox/")
  return data
}

export async function createSharedTool(payload: {
  name: string
  item_type: string
  description?: string
  config_json?: object | string
}): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>("/ai/toolbox/create/", {
    name: payload.name,
    item_type: payload.item_type,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

export async function updateSharedTool(
  itemId: number,
  payload: {
    name?: string
    item_type?: string
    description?: string
    config_json?: object | string
  },
): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/update/`, {
    name: payload.name,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

export async function deleteSharedTool(itemId: number): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/delete/`)
  return data
}

export async function toggleSharedTool(itemId: number, enabled: boolean): Promise<AgentOpResponse> {
  const { data } = await djangoClient.post<AgentOpResponse>(`/ai/toolbox/${itemId}/toggle/`, {
    enabled,
  })
  return data
}

export async function uploadSharedSkill(files: File[], name: string): Promise<AgentOpResponse> {
  const formData = new FormData()
  formData.append("name", name)
  for (const file of files) {
    // 服务端框架会把上传文件名归一为 basename，目录层级只能靠 paths 显式提交；
    // files 与 paths 必须保持一一对应的提交顺序
    const relativePath = file.webkitRelativePath || file.name
    formData.append("files", file, relativePath)
    formData.append("paths", relativePath)
  }
  const { data } = await djangoClient.post<AgentOpResponse>("/ai/toolbox/upload-skill/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

export async function fetchSharedSkillTree(name: string): Promise<{
  status: boolean
  data?: { name?: string; tree?: SkillTreeNode[] }
  message?: string
}> {
  const { data } = await djangoClient.get(`/ai/toolbox/skills/${encodeURIComponent(name)}/tree/`)
  return data
}

export async function fetchSharedSkillFile(
  name: string,
  path: string,
): Promise<{ status: boolean; data?: SkillFilePayload; message?: string }> {
  const { data } = await djangoClient.get(`/ai/toolbox/skills/${encodeURIComponent(name)}/file/`, {
    params: { path },
  })
  return data
}

// ── 平台配置（平台唯一智能体的工具配置，AI 工具箱读写） ──

export interface PlatformConfig {
  agent_id?: number
  agent_name?: string
  enable_workspace_tools: boolean
  enable_business_tools: boolean
  enable_mcp_tools: boolean
  enable_skills: boolean
  skills_config: Record<string, boolean>
}

export async function fetchPlatformConfig(): Promise<{
  status: boolean
  data?: PlatformConfig
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/platform-config/")
  return data
}

export async function updatePlatformConfig(
  payload: Partial<PlatformConfig>,
): Promise<{ status: boolean; data?: PlatformConfig; message?: string }> {
  const { data } = await djangoClient.post("/ai/platform-config/update/", payload)
  return data
}

// ── 单模型调试（工具箱「模型调试」）──

export type ModelDebugRole = "planner" | "executor" | "verifier"

export interface ModelDebugTool {
  name: string
  read_only: boolean
  category: string
  enabled: boolean
}

export interface ModelDebugModelSummary {
  provider: string
  model_name: string
  has_api_key: boolean
  configured: boolean
}

export interface ModelDebugRoleConfig {
  role: ModelDebugRole
  label: string
  vision: boolean
  /** 该角色工具子集里是否有工具需要设备（决定页内是否必须选设备） */
  needs_device: boolean
  model: ModelDebugModelSummary
  tools: ModelDebugTool[]
}

export interface ModelDebugSkills {
  gate_on: boolean
  shared_by_roles: boolean
  items: { name: string; path: string }[]
}

export interface ModelDebugConfig {
  agent_id: number
  agent_name: string
  role: ModelDebugRoleConfig
  skills: ModelDebugSkills
}

/** 引擎回溯出的工具调用/返回记录（type=call 带 input，type=result 带 output/state） */
export interface ModelDebugToolCall {
  type: "call" | "result"
  name: string
  input?: Record<string, unknown>
  output?: string
  state?: string
}

export interface ModelDebugReply {
  role: ModelDebugRole
  label: string
  model_name: string
  reply: string
  thinking?: string[]
  /** 本轮工具调用轨迹（调试对话挂真实工具，故会非空） */
  tool_usage?: ModelDebugToolCall[]
  /** 本轮设备点击证据（平台装配；无副作用点击时缺省） */
  log_check?: TaskLogCheck
  /** 验收角色的调试日志证据（平台按取证基准从日志文件回溯取出；取不到时缺省） */
  log_evidence?: TaskLogEvidence
  /** 该证据的取证基准（基准时刻 / 来源 / 读取的文件 / 无日志时的原因） */
  log_basis?: ModelDebugLogBasis
  /** 本轮检查的日志关键词（平台按 check_device_log 的调用自动填；没检查过则缺省） */
  log_assertion_info?: string
  usage?: Record<string, number>
  cost?: number
}

export async function fetchModelDebugConfig(
  role: ModelDebugRole | string,
): Promise<{ status: boolean; data?: ModelDebugConfig; message?: string }> {
  const { data } = await djangoClient.get(`/ai/model-debug/${encodeURIComponent(role)}/`)
  return data
}

/** 单角色调试对话：挂该角色真实工具，可能真机操作，故不设等待上限（serial 条件必填） */
export async function chatWithModelDebug(
  role: ModelDebugRole | string,
  text: string,
  serial = "",
): Promise<{ status: boolean; data?: ModelDebugReply; message?: string }> {
  const { data } = await djangoClient.post(`/ai/model-debug/${encodeURIComponent(role)}/chat/`, {
    text,
    serial,
  })
  return data
}

// ── Platform tools ──

export interface PlatformToolItem {
  name: string
  summary: string
  icon: string
  read_only: boolean
  enabled: boolean
}

export interface PlatformToolCategory {
  key: string
  icon: string
  color: string
  tools: PlatformToolItem[]
}

export async function fetchPlatformTools(): Promise<{
  status: boolean
  data?: { categories?: PlatformToolCategory[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/available-tools/")
  return data
}

export async function togglePlatformTool(payload: {
  name?: string
  category?: string
  enabled: boolean
}): Promise<{ status: boolean; data?: { updated?: string[] }; message?: string }> {
  const { data } = await djangoClient.post("/ai/platform-tools/toggle/", payload)
  return data
}

// ── 平台工具调试（JWT schema + invoke，禁止走 /ai/tools/ 内部网关）──

export interface PlatformToolOption {
  /** 可直接提交的取值（如设备序列号） */
  value: string
  /** 展示标签（设备名称/型号 + 序列号） */
  label: string
}

export interface PlatformToolParamSchema {
  name: string
  /** 参数中文名（服务端集中维护；未登记时回退为英文参数名） */
  label: string
  /** 参数中文说明（取自工具 docstring 的 Args 段；无则为空串） */
  hint: string
  type: "str" | "int" | "float" | "bool" | string
  required: boolean
  default?: unknown
  /** 服务端按请求者可见性给出的候选值；缺省 = 自由输入 */
  options?: PlatformToolOption[]
}

export interface PlatformToolDebugSchema {
  name: string
  summary: string
  read_only: boolean
  parameters: PlatformToolParamSchema[]
}

export async function fetchPlatformToolSchema(
  name: string,
): Promise<{ status: boolean; data?: PlatformToolDebugSchema; message?: string }> {
  const { data } = await djangoClient.get(`/ai/platform-tools/${encodeURIComponent(name)}/`)
  return data
}

export async function invokePlatformTool(
  name: string,
  params: Record<string, unknown> = {},
): Promise<{ status: boolean; data?: { result?: unknown }; message?: string }> {
  const { data } = await djangoClient.post(
    `/ai/platform-tools/${encodeURIComponent(name)}/invoke/`,
    params,
  )
  return data
}

export async function fetchAvailableSkills(): Promise<{
  status: boolean
  data?: { skills?: object[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/available-skills/")
  return data
}

// ── 无线端口管理（监听开关 + 当前日志文件读取；见 openspec device-log-port-console）──

export interface LogPortRow {
  port: number
  /** SKU名称（被测设备型号，如 H6810） */
  sku: string
  /** 无线串口盒串口侧波特率（仅展示，不参与采集） */
  baud: number
  /** 监听开关：平台是否持续监听该端口 */
  enabled: boolean
  /** 运行时状态：端口此刻是否真的在监听 */
  listening: boolean
  log_file: string
  size_bytes: number
  note: string
}

export interface LogPortLine {
  timestamp: string
  source: string
  text: string
}

export interface LogPortLinesPayload {
  port: number
  sku: string
  log_file: string
  tail: number
  line_count: number
  raw_line_count: number
  /** 服务端已按「同毫秒合并、最新在上」排好：前端 MUST NOT 再排序 */
  lines: LogPortLine[]
  conclusion: "ok" | "no_log" | "port_not_configured" | "port_disabled" | string
  note: string
}

export async function fetchLogPorts(): Promise<{
  status: boolean
  data?: { ports?: LogPortRow[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/log-ports/")
  return data
}

export async function toggleLogPort(
  port: number,
  enabled: boolean,
): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.post("/ai/log-ports/toggle/", { port, enabled })
  return data
}

export async function fetchLogPortLines(
  port: number,
  tail: number,
): Promise<{ status: boolean; data?: LogPortLinesPayload; message?: string }> {
  const { data } = await djangoClient.get(`/ai/log-ports/${port}/lines/`, { params: { tail } })
  return data
}

// ── 日志关键词目录（工具箱「日志关键词」来源，只读）──

/** 关键词命中的功能点（编号 + 模块 + 名称） */
export interface LogKeywordFeature {
  id?: number
  module?: string
  feature?: string
}

export interface LogKeywordEntry {
  keyword: string
  /** 一个关键词可对应多个功能点，全部带出 */
  features: LogKeywordFeature[]
}

export interface LogKeywordCatalog {
  keywords: LogKeywordEntry[]
  keyword_count: number
  feature_count: number
  /** 取值来源：运行中的采集索引 / 配置文件 / 都取不到 */
  origin: "runtime" | "file" | "none" | string
  keyword_file: string
  updated_at: string
  note: string
}

export async function fetchLogKeywords(): Promise<{
  status: boolean
  data?: LogKeywordCatalog
  message?: string
}> {
  const { data } = await djangoClient.get("/ai/log-keywords/")
  return data
}
