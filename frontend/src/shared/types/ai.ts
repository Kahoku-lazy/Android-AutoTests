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
  available_models?: string[]
  tags?: string[]
  description?: string
  avatar_url?: string
  avatar?: string
  tool_count?: number
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
export interface AgentListResponse {
  status?: boolean
  agents?: AgentRecord[]
  message?: string
}

export interface AgentDetailResponse {
  status?: boolean
  agent?: AgentRecord
  message?: string
}

export interface AgentOpResponse {
  status?: boolean
  message?: string
}

export interface AgentTestResponse {
  status?: boolean
  connected?: boolean
  available_models?: string[]
  message?: string
}

export interface AgentHealthResponse {
  status?: boolean
  agents?: { id: number; is_connected: boolean; last_checked?: string }[]
  message?: string
}

export interface ConversationListResponse {
  status?: boolean
  conversations?: Conversation[]
  message?: string
}

export interface ConversationCreateResponse {
  status?: boolean
  id?: number
  title?: string
  message?: string
}

export interface MessagesResponse {
  status?: boolean
  messages?: ChatMessage[]
  message?: string
}

export interface SaveMessageResponse {
  status?: boolean
  message?: string
}

export interface ToolboxListResponse {
  status?: boolean
  items?: object[]
  message?: string
}

export interface KnowledgeStatusResponse {
  status?: boolean
  doc_count?: number
  db_size_mb?: number
  last_indexed?: string
  running?: boolean
  message?: string
}
