/**
 * 知识库助手模块 DTO 与前端内部类型。
 *
 * 服务端字段保持 snake_case（项目契约），前端只在展示层做 camelCase 计算。
 */

export type VoiceState = "idle" | "connecting" | "listening" | "thinking" | "speaking" | "error"

export type MessageRole = "user" | "assistant"

export type MessageStatus = "streaming" | "done" | "interrupted" | "error"

export interface TranscriptMessage {
  id: string
  role: MessageRole
  text: string
  status: MessageStatus
  at: number
}

export interface KnowledgeAssistantStatus {
  enabled: boolean
  ready: boolean
  reason: string
  mode: string
  model: string
  voice: string
  agent_name: string
  translation_language: string
  pipeline_llm_model?: string
  pipeline_tts_model?: string
  pipeline_tts_voice?: string
  log_dir: string
  log_file: string
}

export interface ReadyEvent {
  type: "ready"
  session_id: string
  agent_name: string
  model: string
  voice: string
  turn_detection: string
  mode: string
  translation_language: string
  input_sample_rate: number
  output_sample_rate: number
  log_path: string
}

export interface ReplyStartEvent {
  type: "reply_start"
  reply_id: string
  role: MessageRole
  name: string
}

export interface TranscriptDeltaEvent {
  type: "transcript_delta"
  reply_id: string
  role: MessageRole
  delta: string
}

export interface TranscriptFinalEvent {
  type: "transcript_final"
  reply_id: string
  role: MessageRole
  text: string
}

export interface ReplyEndEvent {
  type: "reply_end"
  reply_id: string
  role: MessageRole
  reason: string
}

export interface StateEvent {
  type: "state"
  value: string
}

export interface ErrorEvent {
  type: "error"
  message: string
}

export interface NoticeEvent {
  type: "notice"
  message: string
}

export interface AudioItemEvent {
  type: "audio_item"
  item_id: string
}

export interface ClearAudioEvent {
  type: "clear_audio"
}

export interface ClosedEvent {
  type: "closed"
}

export type ServerEvent =
  | ReadyEvent
  | ReplyStartEvent
  | TranscriptDeltaEvent
  | TranscriptFinalEvent
  | ReplyEndEvent
  | StateEvent
  | ErrorEvent
  | NoticeEvent
  | AudioItemEvent
  | ClearAudioEvent
  | ClosedEvent

export interface SessionInfo {
  agentName: string
  model: string
  voice: string
  mode: string
  translationLanguage: string
  logPath: string
}
