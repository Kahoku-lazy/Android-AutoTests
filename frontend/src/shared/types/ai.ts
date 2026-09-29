/** AI 助手模块共享类型 — AgentScope SSE 事件、Agent、对话、消息、工具调用 */

// ── 字面量联合类型 ──

export type ViewMode = "agents" | "toolbox"
export type AgentStatus = "active" | "paused" | "error"
export type ConnectionMode = "sse" | "django" | "connecting" | "unknown"
export type ModelStatus =
  "idle" | "streaming" | "thinking" | "tool_calling" | "calling_model" | "done"
export type MessageRole = "user" | "assistant"
export type DeliveryStatus = "sending" | "sent" | "error"
export type StreamReason = "normal" | "exceed_max_iters" | "stopped" | "error" | "detached"
export type ToolState = "calling" | "submitted" | "running" | "success" | "error" | "denied"

// ── Agent ──
export interface AgentRecord {
  id: number
  name: string
  status: AgentStatus
  model_name?: string
  model_provider?: string
  strong_model_name?: string
  strong_enabled?: boolean
  available_models?: string[]
  tags?: string[]
  description?: string
  avatar_url?: string
  avatar?: string
  tool_count?: number
  route_configs?: RouteConfigMap
}

// ── 多线路模型配置 ──
export interface RouteModelConfig {
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
}

/** 线路连通三态：可执行 / 密钥通但不可用 / 断线 */
export type RouteConnStatus = "ready" | "unusable" | "offline"

export interface RouteHealth {
  is_connected?: boolean | null
  /** ready | unusable | offline；缺省时前端按探测中处理 */
  status?: RouteConnStatus | null
  last_checked_at?: string
  last_checked?: string
  results?: Record<string, RouteModelTestResult>
}

export interface RouteConfig {
  name?: string
  avatar?: string
  planner?: RouteModelConfig
  executor?: RouteModelConfig
  verifier?: RouteModelConfig
  health?: RouteHealth
}

export interface RouteConfigMap {
  device_control?: RouteConfig
}

export type AgentRoute = "device_control"

// ── 任务发布 ──
export interface TaskRecord {
  id: number
  title: string
  goal: string
  status: string
  result?: string
  device_serial?: string
  /** 卡片展示用设备名（型号）；空则前端回退 serial */
  device_label?: string
  /** 当前线路助手名（实时派生，随改名同步） */
  assistant_name?: string
  /** 附件原始文件名（仅文件名，正文只在详情下发） */
  attachment_filename?: string
  created_at?: string
  started_at?: string
  finished_at?: string
  deepseek_cost?: number
}

export interface TaskSubmitPayload {
  title: string
  goal: string
  device_serial?: string
  device_label?: string
}

export interface TaskListResponse {
  status?: boolean
  data?: { tasks: TaskRecord[] }
  message?: string
}

export interface TaskFailedItem {
  item?: string
  reason?: string
  action?: string
  assert?: string
  actual?: string
}

/** 规划步骤：一步一操作 + 一步一断言 */
export interface TaskRunStep {
  action: string
  assert: string
}

export interface TaskRunToolTrace {
  type: string
  name?: string
  input?: string
  /** 工具返回摘要（已脱敏，截图仅路径） */
  output?: string
  state?: string
  media_type?: string
  /** screenshot_page 落盘相对路径 */
  screenshot_path?: string
}

export interface TaskRunRoleTrace {
  /** 发给该角色的输入 prompt */
  input?: string
  thinking?: string[]
  tools?: TaskRunToolTrace[]
  /** 角色最终文本输出 */
  text?: string
}

export interface TaskRunExecutorOut {
  result?: string
  /** 点击前的时间戳（新执行契约；存量旧记录没有该键） */
  click_timer?: string
  /** 点击后截图的相对路径（新执行契约；无截图时为空串） */
  screenshot?: string
  /** 存量旧记录：执行的操作 */
  action?: string
  /** 存量旧记录：模型写的说明文字 */
  message?: string
}

export interface TaskRunVerifierOut {
  /** 验收结论：新契约为 PASS/FAIL 字符串，存量旧记录为 boolean */
  result?: boolean | string
  /** 点击前的时间戳（新验收契约；存量旧记录没有该键） */
  click_timer?: string
  /** 检测到日志关键词的时间戳（新验收契约；未检测到为空串） */
  logAssertionTimer?: string
  /** 本轮检查的日志关键词（新验收契约；平台按检查工具调用自动填） */
  logAssertionInfo?: string
  /** 验证截图的相对路径（新验收契约；未取到路径为空串） */
  screenshot?: string
  /** 实际结果说明（截图里真实看到了什么） */
  actual?: string
  /** 存量旧记录：被验证的操作 */
  action?: string
  /** 存量旧记录：断言 */
  assert?: string
  summary?: string
  completed?: string[]
  failed?: TaskFailedItem[]
}

/** 设备日志证据：命中的功能点（关键词 → 功能模块 / 功能点） */
export interface TaskLogFeature {
  id?: number
  module?: string
  feature?: string
}

/** 设备日志证据：某个关键词的一次出现（那一刻的原文） */
export interface TaskLogOccurrence {
  timestamp?: string
  source?: string
  text?: string
  grade?: string
}

/** 设备日志证据：窗口原始日志行（同毫秒已合并，text 内保留换行） */
export interface TaskLogLine {
  timestamp?: string
  source?: string
  text?: string
  port?: number
}

/** 设备日志证据：某个关键词的命中块 */
export interface TaskLogEvidenceHit {
  keyword?: string
  /** strong（强证据）/ periodic（疑似周期，不能单独作为通过依据）/ before_action / out_of_window */
  grade?: string
  count?: number
  timestamps?: string[]
  occurrences?: TaskLogOccurrence[]
  features?: TaskLogFeature[]
  baseline_occurrences?: Array<{ timestamp?: string; text?: string }>
}

/** 设备日志证据：某步的验收取证块（引擎写入过程记录，页面只读展示） */
export interface TaskLogEvidence {
  channel?: string
  window_id?: string
  window_opened_at?: string
  action_time?: string
  action_times?: string[]
  threshold_seconds?: number
  baseline_seconds?: number
  window_line_count?: number
  /** hit / no_hit / no_log / out_of_window */
  conclusion?: string
  hits?: TaskLogEvidenceHit[]
  before_action?: Array<{ keyword?: string; timestamp?: string; text?: string; grade?: string }>
  out_of_window?: Array<{
    keyword?: string
    timestamp?: string
    text?: string
    grade?: string
    delta_seconds?: number
  }>
  /** 窗口原始日志（服务端已按「同毫秒合并 + 最新在上」排好，前端 MUST NOT 再排序） */
  lines?: TaskLogLine[]
}

/** 模型调试：本轮日志证据的取证基准（平台从消息里识别，或退回「最近一个取证窗」） */
export interface ModelDebugLogBasis {
  /** 实际使用的取证基准时刻（北京时间毫秒） */
  basis_time?: string
  /** true = 基准取自消息里的时间戳；false = 退回最近一个取证窗 */
  from_message?: boolean
  /** 实际读取的日志文件路径文本 */
  files?: string[]
  /** 取不到窗口内日志时的如实原因；取到则为空串 */
  note?: string
}

/** 执行侧点击证据：一次副作用点击（点击前时间点 + 点击后截图路径，未截图时为空串） */
export interface TaskLogCheckClick {
  action_time?: string
  screenshot_path?: string
}

/** 执行侧点击证据块（引擎写入过程记录；log 只在「本步断言需日志核对」时非空） */
export interface TaskLogCheck {
  clicks?: TaskLogCheckClick[]
  /** 与该步验收证据同源的 5 秒窗口证据（不需日志核对的步骤为空） */
  log?: TaskLogEvidence | null
}

/** 过程日志：一步一次重试 */
export interface TaskRunLogEntry {
  action?: string
  assert?: string
  loop: number
  executor?: string | TaskRunExecutorOut
  verifier?: TaskRunVerifierOut
  /** 验收证据截图（相对 MEDIA，如 ai_tasks/12/s2_l1.jpg） */
  screenshot?: string
  /** 本步的验收设备日志证据（老任务 / 未采集时缺省） */
  log_evidence?: TaskLogEvidence
  /** 本步执行侧的点击证据（老任务 / 本步无点击且不需日志时缺省） */
  executor_log_check?: TaskLogCheck
  executor_trace?: TaskRunRoleTrace
  verifier_trace?: TaskRunRoleTrace
  /** @deprecated 旧协议按目标聚合 */
  goal?: string
  steps?: Array<string | TaskRunStep>
  verification?: string
  result?: string
}

export interface TaskRunPlan {
  goal: string
  steps?: Array<string | TaskRunStep>
  /** @deprecated 旧协议目标级验收 */
  verification?: string
}

export interface TaskRunPayload {
  status?: string
  summary?: string
  reason?: string
  message?: string
  completed?: string[]
  failed?: TaskFailedItem[]
  plans?: TaskRunPlan[]
  log?: TaskRunLogEntry[]
  usage?: Record<string, unknown>
  models?: { planner?: string; executor?: string; verifier?: string; max_loops?: number }
  max_loops?: number
}

export interface TaskDetail {
  id: number
  title: string
  goal: string
  status: string
  device_serial?: string
  device_label?: string
  assistant_name?: string
  attachment_filename?: string
  /** 附件解析后的 Markdown 正文全文；无附件为空串 */
  attachment?: string
  /** 引擎实际交给规划模型的四键 JSON 原文（与装配同源派生） */
  planner_input?: string
  created_at?: string
  started_at?: string
  finished_at?: string
  input_tokens?: number
  output_tokens?: number
  cache_input_tokens?: number
  model_usage?: Record<
    string,
    { input_tokens?: number; output_tokens?: number; cache_input_tokens?: number }
  >
  deepseek_cost?: number
  run?: TaskRunPayload
}

export interface TaskDetailResponse {
  status?: boolean
  data?: TaskDetail
  message?: string
}

export interface TaskDeleteResponse {
  status?: boolean
  message?: string
}

export interface TaskSubmitResponse {
  status?: boolean
  data?: { id?: number; status?: string; result?: string }
  message?: string
}

// ── Conversation ──
export interface Conversation {
  id: number
  title: string
  status: string
}

// ── Content Blocks ──
export interface ContentBlock {
  type: string
  id?: string
  [key: string]: unknown
}

export interface TextBlock extends ContentBlock {
  type: "text"
  text: string
}

export interface ThinkingBlock extends ContentBlock {
  type: "thinking"
  thinking: string
  done?: boolean
  roundIndex?: number
}

export interface ToolCallBlock extends ContentBlock {
  type: "tool_call"
  name: string
  input?: object
  inputRaw?: string
  state: string
  roundIndex?: number
}

export interface ToolResultBlock extends ContentBlock {
  type: "tool_result"
  name: string
  output: string
  state: string
}

export interface ToolPairBlock extends ContentBlock {
  type: "tool_pair"
  call: ToolCallBlock
  result: ToolResultBlock
}

export interface HintBlock extends ContentBlock {
  type: "hint"
  hint: string | object
  source?: string
}

// ── Tool Call (UI state) ──
export interface ToolCall {
  id: string
  name: string
  state: ToolState
  displayArgs?: string
  input?: object
  inputRaw?: string
  output?: string
  resultImage?: string
  partialOutput?: string | null
  roundIndex?: number
  source?: "builtin" | "platform" | "mcp" | "skill"
  startedAt?: number
}

// ── SSE Round (ReAct per-round) ──
export interface SSERound {
  thinking: string
  thinkingDone: boolean
  thinkingExpanded?: boolean
  tools: ToolCall[]
  _pending?: string
}

// ── Chat Message ──
export interface ChatMessage {
  id?: number | string
  role: MessageRole
  content: string
  blocks?: ContentBlock[]
  flow?: string | null
  tokens?: number
  inputTokens?: number
  modelName?: string
  model_name?: string
  created_at?: string
  thinking?: string
  thinkingDone?: boolean
  thinkingExpanded?: boolean
  toolFlow?: ToolCall[]
  rounds?: SSERound[]
  hint?: object | string | null
  reason?: StreamReason
  deliveryStatus?: DeliveryStatus
}

// ── HITL Confirm Event ──
export interface HitlToolCall {
  tool_call_id: string
  tool_call_name?: string
  arguments?: string | object
}

export interface HitlConfirmEvent {
  replyId?: string
  toolCalls?: HitlToolCall[]
}

// ── API 响应（宽松 interface — strict:false 下字面量判别属性会被拓宽，union 窄化失效）
// Agents 组（Batch 1 已迁 DRF）：信封 {status, data}；其余端点（conversations 等）待迁移，暂保持平铺。
export interface AgentListResponse {
  status?: boolean
  data?: { agents: AgentRecord[] }
  message?: string
}

export interface AgentDetailResponse {
  status?: boolean
  data?: { agent: AgentRecord }
  message?: string
}

export interface AgentOpResponse {
  status?: boolean
  data?: { id?: number }
  message?: string
}

export interface RouteModelTestResult {
  connected?: boolean
  /** 密钥能否访问供应商（list 或等价鉴权） */
  key_ok?: boolean
  model_name?: string
  message?: string
}

export interface AgentTestResponse {
  status?: boolean
  data?: {
    connected?: boolean
    /** 线路三态；与 connected（仅 ready）对齐 */
    status?: RouteConnStatus
    available_models?: string[]
    message?: string
    results?: Record<string, RouteModelTestResult>
    last_checked?: string
  }
  message?: string
}

export interface AgentHealthResponse {
  status?: boolean
  data?: {
    agents: {
      id: number
      is_connected: boolean
      last_checked?: string
      routes?: Record<string, RouteHealth>
    }[]
  }
  message?: string
}

// Conversations 组（Batch 2 已迁 DRF）：信封 {status, data}；toolbox 待迁移，暂保持平铺。
export interface ConversationListResponse {
  status?: boolean
  data?: { conversations: Conversation[] }
  message?: string
}

export interface ConversationCreateResponse {
  status?: boolean
  data?: { id?: number; title?: string; agent_scope_session_id?: string }
  message?: string
}

export interface MessagesResponse {
  status?: boolean
  data?: { messages: ChatMessage[] }
  message?: string
}

export interface SaveMessageResponse {
  status?: boolean
  data?: { id?: number }
  message?: string
}

// Toolbox（Batch 3 已迁 DRF）：信封 {status, data}。
export interface ToolboxListResponse {
  status?: boolean
  data?: { items: object[] }
  message?: string
}
