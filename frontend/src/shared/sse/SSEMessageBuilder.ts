/** SSEMessageBuilder — AgentScope 2.0 SSE 事件 → UI 块状态机。
 *
 *  从 ai-assistant/api.js 提取为共享基础设施。
 *  处理 25 种 AgentScope SSE 事件，增量构建有序 blocks[] 数组。
 *
 *  Verified against agentscope/event/_event.py EventType StrEnum.
 */
import type { ContentBlock } from '@/shared/types/ai'

// ── AgentScope 2.0 Event Types (matches agentscope/event/_event.py) ──
export const EventType = {
  REPLY_START:               'REPLY_START',
  REPLY_END:                 'REPLY_END',
  EXCEED_MAX_ITERS:          'EXCEED_MAX_ITERS',
  MODEL_CALL_START:          'MODEL_CALL_START',
  MODEL_CALL_END:            'MODEL_CALL_END',
  TEXT_BLOCK_START:          'TEXT_BLOCK_START',
  TEXT_BLOCK_DELTA:          'TEXT_BLOCK_DELTA',
  TEXT_BLOCK_END:            'TEXT_BLOCK_END',
  DATA_BLOCK_START:          'DATA_BLOCK_START',
  DATA_BLOCK_DELTA:          'DATA_BLOCK_DELTA',
  DATA_BLOCK_END:            'DATA_BLOCK_END',
  THINKING_BLOCK_START:      'THINKING_BLOCK_START',
  THINKING_BLOCK_DELTA:      'THINKING_BLOCK_DELTA',
  THINKING_BLOCK_END:        'THINKING_BLOCK_END',
  HINT_BLOCK:                'HINT_BLOCK',
  TOOL_CALL_START:           'TOOL_CALL_START',
  TOOL_CALL_DELTA:           'TOOL_CALL_DELTA',
  TOOL_CALL_END:             'TOOL_CALL_END',
  TOOL_RESULT_START:         'TOOL_RESULT_START',
  TOOL_RESULT_TEXT_DELTA:    'TOOL_RESULT_TEXT_DELTA',
  TOOL_RESULT_DATA_DELTA:    'TOOL_RESULT_DATA_DELTA',
  TOOL_RESULT_END:           'TOOL_RESULT_END',
  REQUIRE_USER_CONFIRM:      'REQUIRE_USER_CONFIRM',
  REQUIRE_EXTERNAL_EXECUTION:'REQUIRE_EXTERNAL_EXECUTION',
  USER_CONFIRM_RESULT:       'USER_CONFIRM_RESULT',
  EXTERNAL_EXECUTION_RESULT: 'EXTERNAL_EXECUTION_RESULT',
  CUSTOM:                    'CUSTOM',
} as const

export type SSEEventType = typeof EventType[keyof typeof EventType]

// ── Internal accumulator types ──
interface ToolCallAccum { id: string; name: string; argsJson: string; state: string; input?: object; inputRaw?: string }
interface ToolResultAccum { id: string; name: string; output: string; state: string; data?: string; mediaType?: string }
interface DataAccum { data: string; media_type: string }

// ── Process result types ──
export interface SSEProcessResult {
  phase: string
  [key: string]: unknown
}

// ── Builder class ──
export class SSEMessageBuilder {
  blocks: ContentBlock[]
  toolCalls: ToolCallAccum[]
  toolResults: ToolResultAccum[]
  hints: ContentBlock[]
  replyId: string | null
  sessionId: string | null
  name: string | null
  modelName: string | null
  inputTokens: number
  outputTokens: number
  finished: boolean
  exceedMaxIters: boolean

  private _text: Map<string, string>
  private _thinking: Map<string, string>
  private _data: Map<string, DataAccum>
  private _toolCall: Map<string, ToolCallAccum>
  private _toolResult: Map<string, ToolResultAccum>

  constructor() {
    this.blocks = []
    this.toolCalls = []
    this.toolResults = []
    this.hints = []
    this.replyId = null
    this.sessionId = null
    this.name = null
    this.modelName = null
    this.inputTokens = 0
    this.outputTokens = 0
    this.finished = false
    this.exceedMaxIters = false
    this._text = new Map()
    this._thinking = new Map()
    this._data = new Map()
    this._toolCall = new Map()
    this._toolResult = new Map()
  }

  processEvent(event: { type?: string; [key: string]: unknown }): SSEProcessResult {
    const type = event.type
    if (!type) return { phase: 'unknown' }

    // ── Lifecycle ──
    if (type === EventType.REPLY_START) {
      this.replyId = event.reply_id as string
      this.sessionId = event.session_id as string
      this.name = event.name as string
      return { phase: 'reply_start', replyId: event.reply_id, name: event.name, sessionId: event.session_id }
    }
    if (type === EventType.REPLY_END) {
      this.finished = true
      return { phase: 'reply_end', replyId: event.reply_id }
    }
    if (type === EventType.EXCEED_MAX_ITERS) {
      this.exceedMaxIters = true
      return { phase: 'exceed_max_iters', replyId: event.reply_id, name: event.name }
    }

    // ── Model call ──
    if (type === EventType.MODEL_CALL_START) {
      this.modelName = event.model_name as string
      return { phase: 'model_call_start', modelName: event.model_name }
    }
    if (type === EventType.MODEL_CALL_END) {
      this.inputTokens = (event.input_tokens as number) || 0
      this.outputTokens = (event.output_tokens as number) || 0
      return { phase: 'model_call_end', inputTokens: this.inputTokens, outputTokens: this.outputTokens }
    }

    // ── Thinking block ──
    if (type === EventType.THINKING_BLOCK_START) {
      this._thinking.set(event.block_id as string, '')
      return { phase: 'thinking_start', blockId: event.block_id }
    }
    if (type === EventType.THINKING_BLOCK_DELTA) {
      const cur = this._thinking.get(event.block_id as string) || ''
      const next = cur + ((event.delta as string) || '')
      this._thinking.set(event.block_id as string, next)
      return { phase: 'thinking_delta', delta: event.delta || '', blockId: event.block_id, thinking: next }
    }
    if (type === EventType.THINKING_BLOCK_END) {
      const text = this._thinking.get(event.block_id as string) || ''
      this._thinking.delete(event.block_id as string)
      const block: ContentBlock = { type: 'thinking', id: event.block_id as string, thinking: text }
      this.blocks.push(block)
      return { phase: 'thinking_end', blockId: event.block_id, block, thinking: text }
    }

    // ── Text block ──
    if (type === EventType.TEXT_BLOCK_START) {
      this._text.set(event.block_id as string, '')
      return { phase: 'text_start', blockId: event.block_id }
    }
    if (type === EventType.TEXT_BLOCK_DELTA) {
      const cur = this._text.get(event.block_id as string) || ''
      const next = cur + ((event.delta as string) || '')
      this._text.set(event.block_id as string, next)
      return { phase: 'text_delta', delta: event.delta || '', blockId: event.block_id, text: next }
    }
    if (type === EventType.TEXT_BLOCK_END) {
      const text = this._text.get(event.block_id as string) || ''
      this._text.delete(event.block_id as string)
      const block: ContentBlock = { type: 'text', id: event.block_id as string, text }
      this.blocks.push(block)
      return { phase: 'text_end', blockId: event.block_id, block, text }
    }

    // ── Data block ──
    if (type === EventType.DATA_BLOCK_START) {
      this._data.set(event.block_id as string, { data: '', media_type: event.media_type as string })
      return { phase: 'data_start', blockId: event.block_id, mediaType: event.media_type }
    }
    if (type === EventType.DATA_BLOCK_DELTA) {
      const cur = this._data.get(event.block_id as string) || { data: '', media_type: event.media_type as string }
      cur.data += (event.data as string) || ''
      cur.media_type = (event.media_type as string) || cur.media_type
      this._data.set(event.block_id as string, cur)
      return { phase: 'data_delta', blockId: event.block_id, mediaType: cur.media_type }
    }
    if (type === EventType.DATA_BLOCK_END) {
      const cur = this._data.get(event.block_id as string) || { data: '', media_type: '' }
      this._data.delete(event.block_id as string)
      const block: ContentBlock = { type: 'data', id: event.block_id as string, data: cur.data, media_type: cur.media_type }
      this.blocks.push(block)
      return { phase: 'data_end', blockId: event.block_id, block }
    }

    // ── Tool call ──
    if (type === EventType.TOOL_CALL_START) {
      this._toolCall.set(event.tool_call_id as string, {
        id: event.tool_call_id as string,
        name: event.tool_call_name as string,
        argsJson: '',
        state: 'calling',
      })
      return { phase: 'tool_call_start', toolCallId: event.tool_call_id, name: event.tool_call_name }
    }
    if (type === EventType.TOOL_CALL_DELTA) {
      const cur = this._toolCall.get(event.tool_call_id as string)
      if (cur) {
        cur.argsJson += (event.delta as string) || ''
        return { phase: 'tool_call_delta', toolCallId: event.tool_call_id, delta: event.delta, argsJson: cur.argsJson }
      }
      return { phase: 'tool_call_delta', toolCallId: event.tool_call_id, delta: event.delta }
    }
    if (type === EventType.TOOL_CALL_END) {
      const cur = this._toolCall.get(event.tool_call_id as string)
      if (cur) {
        cur.state = 'submitted'
        let parsedInput: object = {}
        try { parsedInput = JSON.parse(cur.argsJson || '{}') } catch { /* ignore parse errors */ }
        cur.input = parsedInput
        cur.inputRaw = cur.argsJson
        const block: ContentBlock = { type: 'tool_call', id: cur.id, name: cur.name, input: cur.input, inputRaw: cur.inputRaw, state: 'submitted' }
        this.toolCalls.push(cur)
        this.blocks.push(block)
        return { phase: 'tool_call_end', toolCall: block }
      }
      return { phase: 'tool_call_end', toolCallId: event.tool_call_id }
    }

    // ── Tool result ──
    if (type === EventType.TOOL_RESULT_START) {
      this._toolResult.set(event.tool_call_id as string, {
        id: event.tool_call_id as string,
        name: event.tool_call_name as string,
        output: '',
        state: 'running',
      })
      const tc = this._toolCall.get(event.tool_call_id as string)
      if (tc) tc.state = 'running'
      return { phase: 'tool_result_start', toolCallId: event.tool_call_id, name: event.tool_call_name }
    }
    if (type === EventType.TOOL_RESULT_DATA_DELTA) {
      // 数据型工具结果（图片/音频等）——累积到独立字段，完整数据随 block 落库，不静默丢弃
      const cur = this._toolResult.get(event.tool_call_id as string)
      if (cur) {
        cur.data = (cur.data || '') + ((event.delta as string) || '')
        cur.mediaType = (event.media_type as string) || cur.mediaType || 'data'
        return { phase: 'tool_result_data_delta', toolCallId: event.tool_call_id, delta: event.delta, mediaType: cur.mediaType }
      }
      return { phase: 'tool_result_data_delta', toolCallId: event.tool_call_id, delta: event.delta }
    }
    if (type === EventType.TOOL_RESULT_TEXT_DELTA) {
      const cur = this._toolResult.get(event.tool_call_id as string)
      if (cur) {
        cur.output += (event.delta as string) || ''
        return { phase: 'tool_result_delta', toolCallId: event.tool_call_id, delta: event.delta, output: cur.output }
      }
      return { phase: 'tool_result_delta', toolCallId: event.tool_call_id, delta: event.delta }
    }
    if (type === EventType.TOOL_RESULT_END) {
      const cur = this._toolResult.get(event.tool_call_id as string)
      const finalState = (event.state as string) || 'success'
      let tr: ContentBlock
      if (cur) {
        cur.state = finalState
        const output = cur.output || (cur.data ? `[数据结果 · ${cur.mediaType || 'data'}]` : '')
        tr = {
          type: 'tool_result', id: cur.id, name: cur.name, output, state: finalState,
          ...(cur.data ? { data: cur.data, mediaType: cur.mediaType || 'data' } : {}),
        }
        this.toolResults.push(cur)
        this._toolResult.delete(event.tool_call_id as string)
      } else {
        tr = { type: 'tool_result', id: event.tool_call_id as string, name: '', output: '', state: finalState }
        this.toolResults.push({ id: event.tool_call_id as string, name: '', output: '', state: finalState })
      }
      const tc = this._toolCall.get(event.tool_call_id as string)
      if (tc) tc.state = finalState
      const pairedBlock: ContentBlock = { type: 'tool_pair', call: tc || { id: event.tool_call_id as string, name: (tr as unknown as { name: string }).name }, result: tr }
      this.blocks.push(pairedBlock)
      return { phase: 'tool_result_end', toolResult: tr, toolCall: tc }
    }

    // ── Hint (one-shot) ──
    if (type === EventType.HINT_BLOCK) {
      const hintText = typeof event.hint === 'string' ? event.hint : JSON.stringify(event.hint)
      const block: ContentBlock = { type: 'hint', id: event.block_id as string, hint: hintText, source: event.source as string | undefined }
      this.hints.push(block)
      this.blocks.push(block)
      return { phase: 'hint', hint: hintText, source: event.source, block }
    }

    // ── Human-in-the-loop ──
    if (type === EventType.REQUIRE_USER_CONFIRM) return { phase: 'require_confirm', toolCalls: event.tool_calls }
    if (type === EventType.REQUIRE_EXTERNAL_EXECUTION) return { phase: 'require_external_exec', toolCalls: event.tool_calls }
    if (type === EventType.USER_CONFIRM_RESULT) return { phase: 'confirm_result', results: event.confirm_results }
    if (type === EventType.EXTERNAL_EXECUTION_RESULT) return { phase: 'external_exec_result', results: event.execution_results }
    if (type === EventType.CUSTOM) return { phase: 'custom', name: event.name, value: event.value }

    return { phase: 'unknown', type, raw: event }
  }

  getBlocks(): ContentBlock[] { return this.blocks }
  getReason(): string { return this.exceedMaxIters ? 'exceed_max_iters' : 'normal' }
  getFullText(): string { return this.blocks.filter(b => b.type === 'text').map(b => (b as unknown as { text: string }).text).join('\n') }
  getFullThinking(): string { return this.blocks.filter(b => b.type === 'thinking').map(b => (b as unknown as { thinking: string }).thinking).join('\n') }

  getToolFlow(): { call: ToolCallAccum; result?: ToolResultAccum }[] {
    return this.toolCalls.map(tc => {
      const result = this.toolResults.find(tr => tr.id === tc.id)
      return { call: tc, result }
    })
  }

  getTokenUsage(): { input: number; output: number; total: number } {
    return { input: this.inputTokens, output: this.outputTokens, total: this.inputTokens + this.outputTokens }
  }
}
