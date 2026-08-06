/** SSE streaming, stop, and HITL confirm handling — TypeScript */
import { ref, nextTick, type Ref } from 'vue'
import client from '@/shared/api-client'
import { ElMessage } from 'element-plus'
import { streamChat } from '../api/sse'
import { logError, logWarn } from '../helpers/logger'
import type { ChatMessage, Conversation, ToolCall, SSERound } from '@/shared/types/ai'
import {
  WORKSPACE_TOOL_NAMES,
  PLATFORM_TOOL_NAMES,
  SSE_WATCHDOG_MS,
  MODEL_STATUS_RESET_MS,
} from '../constants'

/** AI 服务不可用时统一回复文案 */
export const AI_DISCONNECT_MSG = 'AI 服务暂不可用，请检查 Agent 配置后重试'

/** Built-in workspace tool names — used to classify tool source. */
const WORKSPACE_NAMES = new Set(WORKSPACE_TOOL_NAMES)

/** Map known platform tool names → categories for source classification. */
const PLATFORM_NAMES = new Set(PLATFORM_TOOL_NAMES)

function detectToolSource(name: string): ToolCall['source'] {
  if (WORKSPACE_NAMES.has(name)) return 'builtin'
  if (PLATFORM_NAMES.has(name)) return 'platform'
  if (name.startsWith('mcp__')) return 'mcp'
  // Default: treat unknown as mcp (future-proof for user-configured tools)
  return 'mcp'
}

// ── Types ──

interface ToolCallResult {
  id: string
  name?: string
  output?: string
  state?: string
}

interface SSEEventGeneric {
  phase?: string
  delta?: string
  text?: string
  thinking?: string
  toolCallId?: string
  toolCall?: Partial<ToolCall> & { inputRaw?: string }
  toolResult?: ToolCallResult & { state?: string; output?: string }
  modelName?: string
  outputTokens?: number
  inputTokens?: number
  name?: string
  hint?: unknown
  argsJson?: string
  replyId?: string
  toolCalls?: Array<{ tool_call_id: string }>
  block?: { thinking?: string }
  [key: string]: unknown
}

interface PendingConfirm {
  replyId: string
  toolCalls: Array<{ tool_call_id: string }>
}

interface TaskCardHint {
  type: string
  run_id: string
  [key: string]: unknown
}

export interface UseSSEOptions {
  activeConv: Ref<number | null>
  conversations: Ref<Conversation[]>
  messages: Ref<ChatMessage[]>
  assistIdx: Ref<number>
  toolCalls: Ref<ToolCall[]>
  taskCards: Ref<Record<string, TaskCardHint>>
  connectionMode: Ref<string>
  scrollBottom: () => void
  renderMermaidBlocks: () => Promise<void>
  loadConversations: () => Promise<void>
  updateTaskCardProgress: (tr: ToolCallResult) => void
  backgroundStreamConvId: Ref<number | null>
  appendPlaceholder: (displayText: string) => void
}

export interface UseSSEReturn {
  streamMode: Ref<string | null>
  abortController: Ref<AbortController | null>
  sseBuilder: Ref<{ getBlocks: () => object[]; getFullText: () => string; getFullThinking: () => string; getReason: () => string; getTokenUsage: () => { total: number; input: number }; modelName: string } | null>
  modelStatus: Ref<string>
  sending: Ref<boolean>
  pendingConfirm: Ref<PendingConfirm | null>
  pendingConfirmMsgIdx: Ref<number>
  degradedMode: Ref<boolean>
  aiDisconnected: Ref<boolean>
  checkHealth: () => Promise<boolean>
  trySSEStream: (msgText: string) => Promise<void>
  sendStreamMessage: (msgText: string, displayText: string) => Promise<void>
  stopStream: () => void
  detachStream: () => Promise<void>
  resolveConfirm: (toolCallId: string, approved: boolean, reason?: string) => Promise<void>
  approveAll: () => Promise<void>
  denyAll: () => Promise<void>
}

// ── Helpers ──

/** 无内容 / 鉴权失败 / 通道错误 → 视为断线 */
function isDisconnectContent(content: string): boolean {
  const text = String(content || '').trim()
  if (!text || text === AI_DISCONNECT_MSG) return true
  return /API\s*错误\s*\(\s*401\s*\)|authentication_error|api key.*invalid|Authentication Fails|invalid_request_error|请求超时|服务器错误|SSE\s*(subscribe|stream)\s*(failed|error|closed)/i.test(text)
}

interface InternalRound {
  thinking: string
  thinkingDone: boolean
  tools: Partial<ToolCall>[]
  _pending?: string
}

// ── Composable ──

export function useSSE(opts: UseSSEOptions): UseSSEReturn {
  const {
    activeConv, conversations, messages, assistIdx, toolCalls, taskCards,
    connectionMode, scrollBottom, renderMermaidBlocks, loadConversations,
    updateTaskCardProgress, backgroundStreamConvId, appendPlaceholder,
  } = opts

  const streamMode = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)
  const sseBuilder = ref<UseSSEReturn['sseBuilder']>(null)
  const modelStatus = ref('idle')
  const sending = ref(false)
  const pendingConfirm = ref<PendingConfirm | null>(null)
  const pendingConfirmMsgIdx = ref(-1)
  const degradedMode = ref(false)
  const aiDisconnected = ref(false)
  let replyWatchdog: ReturnType<typeof setTimeout> | null = null
  let statusResetTimer: ReturnType<typeof setTimeout> | null = null

  let _detached = false
  let _streamConvId: number | null = null

  function clearReplyWatchdog() {
    if (replyWatchdog) { clearTimeout(replyWatchdog); replyWatchdog = null }
  }
  function clearStatusReset() {
    if (statusResetTimer) { clearTimeout(statusResetTimer); statusResetTimer = null }
  }

  function settleAssistant(content: string, extras: Record<string, unknown> = {}): boolean {
    const disconnected = isDisconnectContent(content)
    aiDisconnected.value = disconnected
    const finalContent = disconnected ? AI_DISCONNECT_MSG : content
    if (assistIdx.value < messages.value.length) {
      const prev = messages.value[assistIdx.value] || {}
      messages.value[assistIdx.value] = {
        ...prev,
        role: 'assistant',
        tokens: prev.tokens || 0,
        ...extras,
        content: finalContent,
        flow: extras.flow === 'sse' ? extras.flow as ChatMessage['flow'] : prev.flow || null,
        reason: disconnected ? 'error' : (extras.reason as ChatMessage['reason']) || prev.reason || 'normal',
      }
    }
    return !disconnected
  }

  async function _savePartialToBackend(reason = 'detached') {
    if (assistIdx.value >= messages.value.length) return
    const msg = messages.value[assistIdx.value]
    if (!msg || msg.role !== 'assistant') return
    const content = msg.content || ''
    const thinking = msg.thinking || ''
    const rounds = msg.rounds || []
    const hasRoundData = rounds.some(r => r.thinking || (r.tools && r.tools.length))
    if (!content && !thinking && !hasRoundData) return
    const convId = _streamConvId || activeConv.value
    if (!convId) return
    try {
      const blocks: object[] = []
      if (hasRoundData) {
        rounds.forEach((round, ri) => {
          if (round.thinking) {
            blocks.push({ type: 'thinking', thinking: round.thinking, done: !!round.thinkingDone, roundIndex: ri + 1 })
          }
          for (const tool of round.tools || []) {
            blocks.push({
              type: 'tool_pair',
              call: { id: tool.id, name: tool.name, inputRaw: (tool as { displayArgs?: string }).displayArgs || '', roundIndex: ri + 1 },
              result: { id: tool.id, name: tool.name, output: tool.output || '', state: tool.state || 'success' },
            })
          }
        })
      } else if (thinking) {
        blocks.push({ type: 'thinking', thinking, done: !!msg.thinkingDone })
      }
      if (content) { blocks.push({ type: 'text', text: content }) }
      await client.post(`/ai/conversations/${convId}/save-message`, {
        role: 'assistant', content, blocks, reason,
        tokens: msg.tokens || 0, input_tokens: (msg as { inputTokens?: number }).inputTokens || 0,
        model_name: (msg as { modelName?: string }).modelName || '', flow: msg.flow || '',
      })
    } catch (e) { console.warn('Failed to save partial message before detach:', e) }
  }

  async function detachStream() {
    if (!sending.value) return
    clearReplyWatchdog()
    await _savePartialToBackend('detached')
    _detached = true
  }

  function finishSending() {
    clearReplyWatchdog()
    sending.value = false; streamMode.value = null; abortController.value = null; modelStatus.value = 'idle'
    if (!_detached) scrollBottom()
    _detached = false
    if (backgroundStreamConvId.value) backgroundStreamConvId.value = null
    _streamConvId = null
  }

  function armReplyWatchdog() {
    clearReplyWatchdog()
    replyWatchdog = setTimeout(async () => {
      if (!sending.value) return
      const cur = messages.value[assistIdx.value]
      if (cur?.role === 'assistant' && !String(cur.content || '').trim()) {
        settleAssistant('')
        const convId = _streamConvId || activeConv.value
        if (convId) {
          try {
            await client.post(`/ai/conversations/${convId}/save-message`, {
              role: 'assistant', content: AI_DISCONNECT_MSG,
              blocks: [{ type: 'text', text: AI_DISCONNECT_MSG }],
              reason: 'error', tokens: 0, input_tokens: 0, model_name: '', flow: '',
            })
          } catch (e) { logWarn('Failed to save watchdog disconnect notice', e, 'useSSE') }
        }
        if (abortController.value) { try { abortController.value.abort() } catch (e) { logError('SSE abort failed', e, 'useSSE') } }
        finishSending()
      }
    }, SSE_WATCHDOG_MS)
  }

  async function checkHealth(): Promise<boolean> {
    try {
      const { data } = await client.get('/ai/agents/health')
      const anyConnected = (data as { agents?: Array<{ is_connected: boolean }> }).agents?.some(a => a.is_connected)
      if (data.status && anyConnected) {
        degradedMode.value = false
      } else if (data.status) {
        degradedMode.value = true
        ElMessage.warning('AI 模型服务暂不可用，请检查 Agent 配置', { duration: 5000 })
      }
    } catch (e) {
      degradedMode.value = true
      logError('Health check failed', e, 'useSSE')
    }
    return degradedMode.value
  }

  async function trySSEStream(msgText: string) {
    _streamConvId = activeConv.value
    _detached = false
    backgroundStreamConvId.value = _streamConvId

    // Agent runs in-process — no separate AgentScope session needed.
    // The SSE endpoint handles everything in a single request.
    const convId = _streamConvId as number

    streamMode.value = 'sse'
    connectionMode.value = 'sse'
    if (assistIdx.value < messages.value.length) {
      messages.value[assistIdx.value].flow = 'sse'
    }

    let streamDone = false
    let fullContent = ''
    let currentToolArgsJson = ''

    const _rounds: InternalRound[] = []
    function _curRound(): InternalRound {
      if (_rounds.length === 0) _rounds.push({ thinking: '', thinkingDone: false, tools: [] })
      return _rounds[_rounds.length - 1]
    }

    let _thinkRaf: number | null = null, _textRaf: number | null = null

    function _flushThink() {
      _thinkRaf = null
      const r = _curRound()
      r.thinking = r._pending || r.thinking
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].rounds = _rounds as SSERound[]
        if (!_detached) scrollBottom()
      }
    }
    function _flushText() {
      _textRaf = null
      if (assistIdx.value < messages.value.length) {
        const dc = isDisconnectContent(fullContent)
        messages.value[assistIdx.value].content = dc ? AI_DISCONNECT_MSG : fullContent
        if (!_detached) scrollBottom()
      }
    }

    const { controller, builder } = streamChat(convId, msgText, {
      onStatus: (status: string) => {
        clearStatusReset()
        modelStatus.value = status
        if (status === 'done') {
          statusResetTimer = setTimeout(() => { if (modelStatus.value === 'done') modelStatus.value = 'idle' }, MODEL_STATUS_RESET_MS)
        }
      },
      onThinkingStart: () => {
        _curRound()._pending = ''
        _curRound().thinking = ''
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].content = fullContent
          if (!_detached) scrollBottom()
        }
      },
      onThinkingDelta: (delta: string, full: string) => {
        const prev = _curRound()._pending || ''
        _curRound()._pending = full || prev + delta
        if (_thinkRaf === null) _thinkRaf = requestAnimationFrame(_flushThink)
      },
      onThinkingEnd: (evt: SSEEventGeneric) => {
        if (_thinkRaf !== null) { cancelAnimationFrame(_thinkRaf); _thinkRaf = null }
        _curRound()._pending = evt?.block?.thinking || _curRound()._pending
        _flushThink()
        _curRound().thinkingDone = true
      },
      onTextDelta: (delta: string, full: string) => {
        fullContent = full != null ? full : fullContent + delta
        if (_textRaf === null) _textRaf = requestAnimationFrame(_flushText)
      },
      onTextEnd: (evt: SSEEventGeneric) => {
        if (_textRaf !== null) { cancelAnimationFrame(_textRaf); _textRaf = null }
        if (evt?.text != null) fullContent = evt.text
        _flushText()
      },
      onToolCallStart: (evt: SSEEventGeneric) => {
        currentToolArgsJson = ''
        const toolName = (evt.name as string) || ''
        toolCalls.value.push({
          id: evt.toolCallId as string,
          name: toolName,
          state: 'calling',
          source: detectToolSource(toolName),
          startedAt: Date.now(),
        })
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
          if (!_detached) scrollBottom()
        }
      },
      onToolCallDelta: (evt: SSEEventGeneric) => {
        currentToolArgsJson = evt.argsJson != null ? evt.argsJson as string : currentToolArgsJson + (evt.delta || '')
      },
      onToolCallEnd: (evt: SSEEventGeneric) => {
        const tc = evt.toolCall
        if (tc) {
          const idx = toolCalls.value.findIndex(t => t.id === tc.id)
          const displayArgs = tc.inputRaw || currentToolArgsJson
          const tagged: ToolCall = {
            ...tc,
            state: 'submitted',
            displayArgs,
            roundIndex: _rounds.length,
            source: detectToolSource(tc.name || ''),
            startedAt: toolCalls.value[idx]?.startedAt,
          } as ToolCall
          if (idx >= 0) toolCalls.value[idx] = tagged
          _curRound().tools.push(tagged)
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
          messages.value[assistIdx.value].rounds = _rounds as SSERound[]
          if (!_detached) scrollBottom()
        }
      },
      onToolResultStart: (evt: SSEEventGeneric) => {
        const idx = toolCalls.value.findIndex(t => t.id === evt.toolCallId)
        if (idx >= 0) toolCalls.value[idx].state = 'running'
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
          if (!_detached) scrollBottom()
        }
      },
      onToolResultDelta: (evt: SSEEventGeneric) => {
        const idx = toolCalls.value.findIndex(t => t.id === evt.toolCallId)
        if (idx >= 0) {
          const tc = toolCalls.value[idx] as ToolCall & { partialOutput?: string | null }
          tc.partialOutput = evt.output != null ? evt.output as string : (tc.partialOutput || '') + (evt.delta || '')
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
          if (!_detached) scrollBottom()
        }
      },
      onToolResultEnd: (evt: SSEEventGeneric) => {
        const tr = evt.toolResult
        if (tr) {
          const idx = toolCalls.value.findIndex(t => t.id === tr.id)
          if (idx >= 0) {
            toolCalls.value[idx].state = tr.state || 'success'
            toolCalls.value[idx].output = tr.output
            ;(toolCalls.value[idx] as ToolCall & { partialOutput?: string | null }).partialOutput = null
          }
          updateTaskCardProgress(tr)
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
          if (!_detached) scrollBottom()
        }
      },
      onModelCallStart: (evt: SSEEventGeneric) => {
        _rounds.push({ thinking: '', thinkingDone: false, tools: [], _pending: '' })
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].modelName = evt.modelName
          messages.value[assistIdx.value].rounds = _rounds as SSERound[]
        }
      },
      onModelCallEnd: (evt: SSEEventGeneric) => {
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].tokens = evt.outputTokens || 0
          ;(messages.value[assistIdx.value] as ChatMessage & { inputTokens?: number }).inputTokens = evt.inputTokens || 0
        }
      },
      onHint: (evt: SSEEventGeneric) => {
        let hintData: unknown = evt.hint
        if (typeof hintData === 'string') { try { hintData = JSON.parse(hintData) } catch { /* empty */ } }
        if ((hintData as TaskCardHint)?.type === 'task_card' && (hintData as TaskCardHint)?.run_id) {
          const td = hintData as TaskCardHint
          const existing = taskCards.value[td.run_id] || {}
          taskCards.value[td.run_id] = { ...existing, ...(td as object), updatedAt: Date.now() } as TaskCardHint
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].hint = hintData as ChatMessage['hint']
          }
          if (!_detached) scrollBottom()
        } else if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].hint = hintData as ChatMessage['hint']
          if (!_detached) scrollBottom()
        }
      },
      onRequireConfirm: (evt: SSEEventGeneric) => {
        modelStatus.value = 'idle'
        pendingConfirm.value = evt as unknown as PendingConfirm
        pendingConfirmMsgIdx.value = assistIdx.value
      },
      onExceedMaxIters: () => {
        if (assistIdx.value < messages.value.length) {
          const allThinking = builder.getFullThinking()
          if (_rounds.length > 0) {
            _curRound().thinking = allThinking || _curRound().thinking
            _curRound().thinkingDone = true
          }
          messages.value[assistIdx.value].thinking = allThinking
          messages.value[assistIdx.value].thinkingDone = true
          messages.value[assistIdx.value].rounds = _rounds as SSERound[]
          messages.value[assistIdx.value].reason = 'exceed_max_iters'
          messages.value[assistIdx.value].content =
            (messages.value[assistIdx.value].content || '') +
            '\n\n⚠️ **[智能体已达最大推理次数]** 响应可能被截断，建议简化问题或分步提问。'
          if (!_detached) scrollBottom()
        }
      },
      onDone: async () => {
        if (streamDone) return
        streamDone = true
        clearReplyWatchdog()
        const finalContent = builder.getFullText() || fullContent
        const blocks = builder.getBlocks()
        const reason = builder.getReason()
        const ok = settleAssistant(finalContent, {
          blocks,
          reason: isDisconnectContent(finalContent) ? 'error' : reason || 'normal',
          tokens: builder.getTokenUsage().total || 0,
          inputTokens: builder.getTokenUsage().input || 0,
          model_name: builder.modelName || '',
          flow: 'sse',
        })
        if (ok) {
          try {
            const saveConvId = _streamConvId || activeConv.value
            await client.post(`/ai/conversations/${saveConvId}/save-message`, {
              role: 'assistant', content: finalContent, blocks, reason,
              tokens: builder.getTokenUsage().total || 0,
              input_tokens: builder.getTokenUsage().input || 0,
              model_name: builder.modelName || '', flow: 'sse',
            })
            if (!_detached) { loadConversations(); await nextTick(); renderMermaidBlocks() }
          } catch (e) { console.error('Failed to save streamed message:', e) }
        }
        finishSending()
      },
      onError: async (err: Error) => {
        if (streamDone) return
        streamDone = true
        clearReplyWatchdog()
        console.warn('SSE stream error:', err)
        modelStatus.value = 'idle'
        settleAssistant('')
        finishSending()
      },
    })

    abortController.value = controller
    sseBuilder.value = builder as unknown as UseSSEReturn['sseBuilder']

    try {
      const convItem = conversations.value.find(c => c.id === activeConv.value)
      if (convItem && convItem.title === '新对话') {
        const { data } = await client.post(`/ai/conversations/${activeConv.value}/rename`, { title: msgText.slice(0, 30) })
        if ((data as { ok?: boolean; title?: string }).status) convItem.title = (data as { title: string }).title
      }
    } catch (e) { console.error(e) }
  }

  async function sendStreamMessage(msgText: string, displayText: string) {
    if (!activeConv.value) return
    sending.value = true
    aiDisconnected.value = false
    toolCalls.value = []
    modelStatus.value = 'calling_model'
    appendPlaceholder(displayText)
    scrollBottom()
    armReplyWatchdog()

    try {
      await trySSEStream(msgText)
    } catch (e) {
      console.warn('SSE setup failed:', e)
      modelStatus.value = 'idle'
      settleAssistant('')
      finishSending()
    }
  }

  function stopStream() {
    clearReplyWatchdog()
    clearStatusReset()
    if (abortController.value) {
      abortController.value.abort()
      if (assistIdx.value < messages.value.length && messages.value[assistIdx.value].flow === 'sse') {
        const partial = messages.value[assistIdx.value].content
        const content = String(partial || '').trim() ? partial : '（用户主动停止）'
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].content = content
          messages.value[assistIdx.value].reason = 'stopped'
        }
        client.post(`/ai/conversations/${_streamConvId || activeConv.value}/save-message`, {
          role: 'assistant', content, tokens: 0, reason: 'stopped',
          blocks: sseBuilder.value ? sseBuilder.value.getBlocks() : [], flow: 'sse',
        }).catch(e => console.error('Failed to save partial stream:', e))
      }
      finishSending()
    }
    pendingConfirm.value = null
  }

  async function resolveConfirm(toolCallId: string, approved: boolean, reason = '') {
    const confirm = pendingConfirm.value
    if (!confirm) return
    if (pendingConfirmMsgIdx.value >= 0 && pendingConfirmMsgIdx.value < messages.value.length) {
      const msg = messages.value[pendingConfirmMsgIdx.value]
      if (!msg.toolFlow) msg.toolFlow = []
      const idx = msg.toolFlow.findIndex(t => t.id === toolCallId)
      if (idx >= 0) {
        msg.toolFlow[idx] = { ...msg.toolFlow[idx], state: approved ? 'submitted' : 'denied' }
      } else {
        msg.toolFlow.push({ id: toolCallId, state: approved ? 'submitted' : 'denied', name: '' })
      }
    }
    pendingConfirm.value = null
    modelStatus.value = 'tool_calling'

    const result = {
      reply_id: confirm.replyId || '',
      confirm_results: [{ tool_call_id: toolCallId, approved, ...(reason ? { reason } : {}) }],
    }
    try {
      await client.post(`/ai/conversations/${activeConv.value}/confirm-result`, result)
    } catch (e) {
      console.error('Failed to send confirm result:', e)
      ElMessage.warning('确认结果发送失败，工具调用可能无法继续')
    }
  }

  async function approveAll() {
    const confirm = pendingConfirm.value
    if (!confirm?.toolCalls) return
    for (const tc of confirm.toolCalls) { await resolveConfirm(tc.tool_call_id, true) }
  }

  async function denyAll() {
    const confirm = pendingConfirm.value
    if (!confirm?.toolCalls) return
    for (const tc of confirm.toolCalls) { await resolveConfirm(tc.tool_call_id, false, '用户拒绝') }
  }

  return {
    streamMode, abortController, sseBuilder, modelStatus, sending,
    pendingConfirm, pendingConfirmMsgIdx, degradedMode, aiDisconnected,
    checkHealth, trySSEStream, sendStreamMessage, stopStream, detachStream,
    resolveConfirm, approveAll, denyAll,
  }
}
