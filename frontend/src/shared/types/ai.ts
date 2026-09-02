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
  platform_task?: RouteConfig
}

export type AgentRoute = 'device_control' | 'platform_task'

// ── 任务发布 ──
export interface TaskRecord {
  id: number
  title: string
  goal: string
  route: AgentRoute
  status: string
  result?: string
  report_name?: string
  device_serial?: string
  created_at?: string
}

export interface TaskSubmitPayload {
  goal: string
  requirements?: string
  attachment?: string
  route: AgentRoute
  report_name?: string
  checklist?: string
  device_serial?: string
}

export interface TaskListResponse {
  status?: boolean
  data?: { tasks: TaskRecord[] }
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
