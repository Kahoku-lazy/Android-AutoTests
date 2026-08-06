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

// ── Task 相关 ──
export type TaskFilterKey = 'all' | 'pending' | 'running' | 'completed' | 'failed'

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
  role: MessageRole
  content: string
  blocks?: ContentBlock[]
  flow?: string | null
  tokens?: number
  inputTokens?: number
  modelName?: string
  thinking?: string
  thinkingDone?: boolean
  toolFlow?: ToolCall[]
  rounds?: SSERound[]
  hint?: object | string | null
  reason?: StreamReason
  deliveryStatus?: DeliveryStatus
}

// ── Task Record ──
export interface TaskRecord {
  run_id: string
  agent_name?: string
  status: string
  title?: string
  task_type?: string
  device_serial?: string
  case_count?: number
  _demo?: boolean
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

// ── Evaluator types ──
export type EvalSubTab = 'self' | 'kb' | 'evalscope' | 'deepeval' | 'maseval'
export type EvalMode = 'benchmark' | 'custom'
export type EvalRunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface QuestionBank {
  id: number
  name: string
  question_count?: number
  category?: string
}

export interface EvalRun {
  id: number
  agent_id?: number
  bank_id?: number
  status: EvalRunStatus
  framework?: string
  score?: number
  created_at?: string
}

// ── API 响应 discriminated unions ──
export type AgentListResponse =
  | { ok: true; agents: AgentRecord[] }
  | { ok: false; error: string }

export type AgentDetailResponse =
  | { ok: true; agent: AgentRecord }
  | { ok: false; error: string }

export type AgentOpResponse =
  | { ok: true }
  | { ok: false; error: string }

export type AgentTestResponse =
  | { ok: true; connected: boolean; available_models: string[] }
  | { ok: false; error: string }

export type AgentHealthResponse =
  | { ok: true; agents: { id: number; is_connected: boolean; last_checked?: string }[] }
  | { ok: false; error: string }

export type ConversationListResponse =
  | { ok: true; conversations: Conversation[] }
  | { ok: false; error: string }

export type ConversationCreateResponse =
  | { ok: true; id: number }
  | { ok: false; error: string }

export type MessagesResponse =
  | { ok: true; messages: ChatMessage[] }
  | { ok: false; error: string }

export type SaveMessageResponse =
  | { ok: true }
  | { ok: false; error: string }

export type ToolboxListResponse =
  | { ok: true; items: object[] }
  | { ok: false; error: string }

export type TaskListResponse =
  | { ok: true; tasks: TaskRecord[] }
  | { ok: false; error: string }

export type KnowledgeStatusResponse =
  | { ok: true; doc_count: number; db_size_mb: number; last_indexed?: string; running: boolean }
  | { ok: false; error: string }
