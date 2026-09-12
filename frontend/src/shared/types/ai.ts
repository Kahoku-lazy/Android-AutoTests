/** AI 助手模块共享类型 — AgentScope SSE 事件、Agent、对话、消息、工具调用 */

// ── 字面量联合类型 ──

export type ViewMode = 'agents' | 'toolbox' | 'knowledge' | 'evaluator'
export type AgentStatus = 'active' | 'paused' | 'error'
export type ConnectionMode = 'sse' | 'django' | 'connecting' | 'unknown'
export type ModelStatus = 'idle' | 'streaming' | 'thinking' | 'tool_calling' | 'calling_model' | 'done'
export type MessageRole = 'user' | 'assistant'
export type DeliveryStatus = 'sending' | 'sent' | 'error'
export type StreamReason = 'normal' | 'exceed_max_iters' | 'stopped' | 'error' | 'detached'
export type ToolState = 'calling' | 'submitted' | 'running' | 'success' | 'error' | 'denied'

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

export interface RouteHealth {
  is_connected?: boolean | null
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

export type AgentRoute = 'device_control'

// ── 任务发布 ──
export interface TaskRecord {
  id: number
  title: string
  goal: string
  status: string
  result?: string
  device_serial?: string
  created_at?: string
}

export interface TaskSubmitPayload {
  goal: string
  attachment?: string
  device_serial?: string
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
  action?: string
  result?: string
  message?: string
}

export interface TaskRunVerifierOut {
  action?: string
  assert?: string
  actual?: string
  /** 新协议为 boolean；旧协议为 pass/fail 字符串 */
  result?: boolean | string
  summary?: string
  completed?: string[]
  failed?: TaskFailedItem[]
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
  created_at?: string
  started_at?: string
  finished_at?: string
  input_tokens?: number
  output_tokens?: number
  cache_input_tokens?: number
  model_usage?: Record<string, { input_tokens?: number; output_tokens?: number; cache_input_tokens?: number }>
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
  type: 'text'
  text: string
}

export interface ThinkingBlock extends ContentBlock {
  type: 'thinking'
  thinking: string
  done?: boolean
  roundIndex?: number
}

export interface ToolCallBlock extends ContentBlock {
  type: 'tool_call'
  name: string
  input?: object
  inputRaw?: string
  state: string
  roundIndex?: number
}

export interface ToolResultBlock extends ContentBlock {
  type: 'tool_result'
  name: string
  output: string
  state: string
}

export interface ToolPairBlock extends ContentBlock {
  type: 'tool_pair'
  call: ToolCallBlock
  result: ToolResultBlock
}

export interface HintBlock extends ContentBlock {
  type: 'hint'
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
  source?: 'builtin' | 'platform' | 'mcp' | 'skill'
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
  model_name?: string
  message?: string
}

export interface AgentTestResponse {
  status?: boolean
  data?: {
    connected?: boolean
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

// Conversations 组（Batch 2 已迁 DRF）：信封 {status, data}；toolbox/knowledge 待迁移，暂保持平铺。
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

// Toolbox / Knowledge（Batch 3 已迁 DRF）：信封 {status, data}。
export interface ToolboxListResponse {
  status?: boolean
  data?: { items: object[] }
  message?: string
}

export interface KnowledgeStatusResponse {
  status?: boolean
  data?: {
    doc_count?: number
    db_size_mb?: number
    reindex?: { running?: boolean; last_indexed?: string | null; message?: string }
  }
  message?: string
}
