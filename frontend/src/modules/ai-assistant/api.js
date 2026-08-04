/** AgentScope SSE streaming and API helpers — v4 (verified against AgentScope 2.0 source).

 * Verified event payload structure (from agentscope/event/_event.py):
 *   - REPLY_START           { type, session_id, reply_id, name, role }
 *   - REPLY_END             { type, session_id, reply_id }
 *   - MODEL_CALL_START      { type, reply_id, model_name }
 *   - MODEL_CALL_END        { type, reply_id, input_tokens, output_tokens }
 *   - TEXT_BLOCK_START      { type, reply_id, block_id }
 *   - TEXT_BLOCK_DELTA      { type, reply_id, block_id, delta }
 *   - TEXT_BLOCK_END        { type, reply_id, block_id }
 *   - THINKING_BLOCK_START  { type, reply_id, block_id }
 *   - THINKING_BLOCK_DELTA  { type, reply_id, block_id, delta }
 *   - THINKING_BLOCK_END    { type, reply_id, block_id }
 *   - DATA_BLOCK_START      { type, reply_id, block_id, media_type }
 *   - DATA_BLOCK_DELTA      { type, reply_id, block_id, data, media_type }
 *   - DATA_BLOCK_END        { type, reply_id, block_id }
 *   - TOOL_CALL_START       { type, reply_id, tool_call_id, tool_call_name }
 *   - TOOL_CALL_DELTA       { type, reply_id, tool_call_id, delta }      ← args JSON fragment
 *   - TOOL_CALL_END         { type, reply_id, tool_call_id }             ← name & args NOT repeated
 *   - TOOL_RESULT_START     { type, reply_id, tool_call_id, tool_call_name }
 *   - TOOL_RESULT_TEXT_DELTA{ type, reply_id, tool_call_id, delta }      ← incremental output
 *   - TOOL_RESULT_DATA_DELTA{ type, reply_id, tool_call_id, block_id, media_type, data|url }
 *   - TOOL_RESULT_END       { type, reply_id, tool_call_id, state }      ← only state, no output
 *   - HINT_BLOCK            { type, reply_id, block_id, source?, hint }
 *   - EXCEED_MAX_ITERS      { type, reply_id, name }
 *   - REQUIRE_USER_CONFIRM  { type, reply_id, tool_calls[] }
 *   - REQUIRE_EXTERNAL_EXECUTION { type, reply_id, tool_calls[] }
 *   - USER_CONFIRM_RESULT   { type, reply_id, confirm_results[] }
 *   - EXTERNAL_EXECUTION_RESULT { type, reply_id, execution_results[] }
 *   - CUSTOM                { type, name, value }
 *
 * Note: ToolCallEndEvent and ToolResultEndEvent do NOT carry name/output.
 *       Caller must reconstruct from Start events + accumulated Deltas.
 *
 * SSE workflow:
 *   1. Create session:    POST /sessions/                    → {session_id}      (Django backend)
 *   2. Subscribe SSE:     GET  /sessions/{session_id}/stream?agent_id=xxx
 *   3. Trigger chat:      POST /chat/                        → fire-and-forget
 */
import djangoClient, { agentscopeClient, getToken } from '@/shared/api-client'

// ── JWT helpers ──
function getUserId() {
  const token = getToken()
  if (!token) return ''
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub || ''
  } catch { return '' }
}

function getAuthHeaders() {
  const token = getToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
}

// ── AgentScope 2.0 Event Types (UPPER_CASE — matches agentscope/event/_event.py EventType StrEnum)
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
}

// ── SSE message builder ──
export class SSEMessageBuilder {
  constructor() {
    this.blocks = []          // ordered content blocks (text, thinking, tool_call, tool_result, data, hint)
    this.toolCalls = []       // tool call blocks (in order)
    this.toolResults = []     // tool result blocks (in order)
    this.hints = []
    this.replyId = null
    this.sessionId = null
    this.name = null
    this.modelName = null
    this.inputTokens = 0
    this.outputTokens = 0
    this.finished = false
    this.exceedMaxIters = false

    // Active accumulators (keyed by id)
    this._text = new Map()    // block_id → string
    this._thinking = new Map()
    this._data = new Map()    // block_id → { data, media_type }
    this._toolCall = new Map()// tool_call_id → { name, argsJson, state, output }
    this._toolResult = new Map()
  }

  processEvent(event) {
    const type = event.type
    if (!type) return { phase: 'unknown' }

    // ── Lifecycle ──
    if (type === EventType.REPLY_START) {
      this.replyId = event.reply_id
      this.sessionId = event.session_id
      this.name = event.name
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
      this.modelName = event.model_name
      return { phase: 'model_call_start', modelName: event.model_name }
    }
    if (type === EventType.MODEL_CALL_END) {
      this.inputTokens = event.input_tokens || 0
      this.outputTokens = event.output_tokens || 0
      return { phase: 'model_call_end', inputTokens: this.inputTokens, outputTokens: this.outputTokens }
    }

    // ── Thinking block ──
    if (type === EventType.THINKING_BLOCK_START) {
      this._thinking.set(event.block_id, '')
      return { phase: 'thinking_start', blockId: event.block_id }
    }
    if (type === EventType.THINKING_BLOCK_DELTA) {
      const cur = this._thinking.get(event.block_id) || ''
      const next = cur + (event.delta || '')
      this._thinking.set(event.block_id, next)
      return { phase: 'thinking_delta', delta: event.delta || '', blockId: event.block_id, thinking: next }
    }
    if (type === EventType.THINKING_BLOCK_END) {
      const text = this._thinking.get(event.block_id) || ''
      this._thinking.delete(event.block_id)
      const block = { type: 'thinking', id: event.block_id, thinking: text }
      this.blocks.push(block)
      return { phase: 'thinking_end', blockId: event.block_id, block, thinking: text }
    }

    // ── Text block ──
    if (type === EventType.TEXT_BLOCK_START) {
      this._text.set(event.block_id, '')
      return { phase: 'text_start', blockId: event.block_id }
    }
    if (type === EventType.TEXT_BLOCK_DELTA) {
      const cur = this._text.get(event.block_id) || ''
      const next = cur + (event.delta || '')
      this._text.set(event.block_id, next)
      return { phase: 'text_delta', delta: event.delta || '', blockId: event.block_id, text: next }
    }
    if (type === EventType.TEXT_BLOCK_END) {
      const text = this._text.get(event.block_id) || ''
      this._text.delete(event.block_id)
      const block = { type: 'text', id: event.block_id, text }
      this.blocks.push(block)
      return { phase: 'text_end', blockId: event.block_id, block, text }
    }

    // ── Data block ──
    if (type === EventType.DATA_BLOCK_START) {
      this._data.set(event.block_id, { data: '', media_type: event.media_type })
      return { phase: 'data_start', blockId: event.block_id, mediaType: event.media_type }
    }
    if (type === EventType.DATA_BLOCK_DELTA) {
      const cur = this._data.get(event.block_id) || { data: '', media_type: event.media_type }
      cur.data += event.data || ''
      cur.media_type = event.media_type || cur.media_type
      this._data.set(event.block_id, cur)
      return { phase: 'data_delta', blockId: event.block_id, mediaType: cur.media_type }
    }
    if (type === EventType.DATA_BLOCK_END) {
      const cur = this._data.get(event.block_id) || { data: '', media_type: '' }
      this._data.delete(event.block_id)
      const block = { type: 'data', id: event.block_id, data: cur.data, media_type: cur.media_type }
      this.blocks.push(block)
      return { phase: 'data_end', blockId: event.block_id, block }
    }

    // ── Tool call (name from START, args from DELTAs) ──
    if (type === EventType.TOOL_CALL_START) {
      this._toolCall.set(event.tool_call_id, {
        id: event.tool_call_id,
        name: event.tool_call_name,
        argsJson: '',
        state: 'calling',
      })
      return { phase: 'tool_call_start', toolCallId: event.tool_call_id, name: event.tool_call_name }
    }
    if (type === EventType.TOOL_CALL_DELTA) {
      const cur = this._toolCall.get(event.tool_call_id)
      if (cur) {
        cur.argsJson += event.delta || ''
        return { phase: 'tool_call_delta', toolCallId: event.tool_call_id, delta: event.delta, argsJson: cur.argsJson }
      }
      return { phase: 'tool_call_delta', toolCallId: event.tool_call_id, delta: event.delta }
    }
    if (type === EventType.TOOL_CALL_END) {
      const cur = this._toolCall.get(event.tool_call_id)
      if (cur) {
        cur.state = 'submitted'
        let parsedInput = {}
        try { parsedInput = JSON.parse(cur.argsJson || '{}') } catch {}
        cur.input = parsedInput
        cur.inputRaw = cur.argsJson
        // Don't delete — keep state until tool_result matches
        const block = { type: 'tool_call', id: cur.id, name: cur.name, input: cur.input, inputRaw: cur.inputRaw, state: 'submitted' }
        this.toolCalls.push(block)
        this.blocks.push(block)
        return { phase: 'tool_call_end', toolCall: block }
      }
      return { phase: 'tool_call_end', toolCallId: event.tool_call_id }
    }

    // ── Tool result (name from START, output from TEXT_DATAs) ──
    if (type === EventType.TOOL_RESULT_START) {
      this._toolResult.set(event.tool_call_id, {
        id: event.tool_call_id,
        name: event.tool_call_name,
        output: '',
        state: 'running',
      })
      // Mark corresponding tool_call as running
      const tc = this._toolCall.get(event.tool_call_id)
      if (tc) tc.state = 'running'
      return { phase: 'tool_result_start', toolCallId: event.tool_call_id, name: event.tool_call_name }
    }
    if (type === EventType.TOOL_RESULT_TEXT_DELTA) {
      const cur = this._toolResult.get(event.tool_call_id)
      if (cur) {
        cur.output += event.delta || ''
        return { phase: 'tool_result_delta', toolCallId: event.tool_call_id, delta: event.delta, output: cur.output }
      }
      return { phase: 'tool_result_delta', toolCallId: event.tool_call_id, delta: event.delta }
    }
    if (type === EventType.TOOL_RESULT_END) {
      const cur = this._toolResult.get(event.tool_call_id)
      const finalState = event.state || 'success'
      let tr
      if (cur) {
        cur.state = finalState
        tr = { type: 'tool_result', id: cur.id, name: cur.name, output: cur.output, state: finalState }
        this.toolResults.push(tr)
        this._toolResult.delete(event.tool_call_id)
      } else {
        tr = { type: 'tool_result', id: event.tool_call_id, name: '', output: '', state: finalState }
        this.toolResults.push(tr)
      }
      // Update tool_call state
      const tc = this._toolCall.get(event.tool_call_id)
      if (tc) tc.state = finalState
      // Pair tool_call with tool_result in blocks
      const pairedBlock = { type: 'tool_pair', call: tc || { id: event.tool_call_id, name: tr.name }, result: tr }
      this.blocks.push(pairedBlock)
      return { phase: 'tool_result_end', toolResult: tr, toolCall: tc }
    }

    // ── Hint (one-shot) ──
    if (type === EventType.HINT_BLOCK) {
      const hintText = typeof event.hint === 'string' ? event.hint : JSON.stringify(event.hint)
      const block = { type: 'hint', id: event.block_id, hint: hintText, source: event.source }
      this.hints.push(block)
      this.blocks.push(block)
      return { phase: 'hint', hint: hintText, source: event.source, block }
    }

    // ── Human-in-the-loop ──
    if (type === EventType.REQUIRE_USER_CONFIRM) {
      return { phase: 'require_confirm', toolCalls: event.tool_calls }
    }
    if (type === EventType.REQUIRE_EXTERNAL_EXECUTION) {
      return { phase: 'require_external_exec', toolCalls: event.tool_calls }
    }
    if (type === EventType.USER_CONFIRM_RESULT) {
      return { phase: 'confirm_result', results: event.confirm_results }
    }
    if (type === EventType.EXTERNAL_EXECUTION_RESULT) {
      return { phase: 'external_exec_result', results: event.execution_results }
    }

    // ── Custom event ──
    if (type === EventType.CUSTOM) {
      return { phase: 'custom', name: event.name, value: event.value }
    }

    return { phase: 'unknown', type, raw: event }
  }

  // Expose the raw blocks array for persistence (跨 Turn 上下文完整性)
  getBlocks() {
    return this.blocks
  }

  // End reason: 'normal' | 'exceed_max_iters' | 'stopped' | 'error'
  getReason() {
    if (this.exceedMaxIters) return 'exceed_max_iters'
    return 'normal'
  }

  getFullText() {
    return this.blocks.filter(b => b.type === 'text').map(b => b.text).join('\n')
  }

  getFullThinking() {
    return this.blocks.filter(b => b.type === 'thinking').map(b => b.thinking).join('\n')
  }

  getToolFlow() {
    return this.toolCalls.map(tc => {
      const result = this.toolResults.find(tr => tr.id === tc.id)
      return { call: tc, result }
    })
  }

  getTokenUsage() {
    return {
      input: this.inputTokens,
      output: this.outputTokens,
      total: this.inputTokens + this.outputTokens,
    }
  }
}


// ── Step 2: Subscribe to SSE stream ──

/**
 * Subscribe to an AgentScope session's SSE event stream.
 * Uses fetch + ReadableStream (not EventSource) for full control over headers and abort.
 */
export function subscribeStream(sessionId, agentScopeId, callbacks = {}) {
  const controller = new AbortController()
  const url = `/agentscope/sessions/${sessionId}/stream?agent_id=${agentScopeId}`
  const builder = new SSEMessageBuilder()

  fetch(url, {
    headers: getAuthHeaders(),
    signal: controller.signal,
  }).then(response => {
    if (!response.ok) {
      throw new Error(`SSE subscribe failed: HTTP ${response.status}`)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          // Stream ended. If REPLY_END already arrived, onDone was called and streamDone is true.
          // If not, this is a premature disconnect → onError.
          // We use a marker set when onDone fires; the caller is expected to abort on completion.
          if (!callbacks._completed) {
            callbacks.onError?.(new Error('SSE stream closed before REPLY_END'))
          }
          return
        }
        buffer += decoder.decode(value, { stream: true })
        // Split on double-newline (SSE event delimiter) to handle multi-line payloads
        const events = buffer.split('\n\n')
        buffer = events.pop()  // last element is the (possibly incomplete) next event

        for (const evtBlock of events) {
          // Each block may have multiple "data:" lines — concatenate them
          const dataLines = []
          for (const line of evtBlock.split('\n')) {
            if (line.startsWith('data: ')) dataLines.push(line.slice(6))
            else if (line.startsWith('data:')) dataLines.push(line.slice(5))
            // comment lines ":..." are silently ignored
          }
          if (!dataLines.length) continue
          try {
            const raw = JSON.parse(dataLines.join('\n'))
            const uiEvent = builder.processEvent(raw)
            if (uiEvent.phase === 'reply_end' || uiEvent.phase === 'exceed_max_iters') {
              callbacks._completed = true
            }
            dispatchUIEvent(uiEvent, raw, callbacks)
          } catch (e) {
            // Non-JSON data — likely heartbeat or error page; ignore silently
            // console.debug('SSE parse error:', e, dataLines)
          }
        }
        read()
      }).catch(err => {
        if (err.name !== 'AbortError') callbacks.onError?.(err)
      })
    }
    read()
  }).catch(err => {
    if (err.name !== 'AbortError') callbacks.onError?.(err)
  })

  return { controller, builder }
}

/** Dispatch a processed UI event to the appropriate callback. */
function dispatchUIEvent(uiEvent, raw, callbacks) {
  const phase = uiEvent.phase
  // Map: 'text_delta' → onTextDelta(delta, text)
  //      'thinking_delta' → onThinkingDelta(delta, thinking)
  //      'tool_call_end' → onToolCallEnd(toolCall)
  //      'tool_result_end' → onToolResultEnd(toolResult)
  if (phase === 'text_delta') {
    callbacks.onTextDelta?.(uiEvent.delta, uiEvent.text)
    callbacks.onStatus?.('streaming')
    return
  }
  if (phase === 'thinking_delta') {
    callbacks.onThinkingDelta?.(uiEvent.delta, uiEvent.thinking)
    callbacks.onStatus?.('thinking')
    return
  }
  // Generic dispatch: on + capitalized phase
  const cbName = 'on' + phase.charAt(0).toUpperCase() + phase.slice(1)
  if (callbacks[cbName]) {
    callbacks[cbName](uiEvent)
  }
  // Stream-completion events: fire onDone so the caller can stop its "sending" spinner.
  // SSE connections stay open indefinitely, so we can't rely on stream `done` to signal completion.
  if (phase === 'reply_end' || phase === 'exceed_max_iters') {
    callbacks.onStatus?.('done')
    callbacks.onDone?.()
  } else if (phase === 'tool_call_start' || phase === 'tool_result_start') {
    callbacks.onStatus?.('tool_calling')
  } else if (phase === 'model_call_start') {
    callbacks.onStatus?.('calling_model')
  }
}


// ── Step 3: Trigger chat (fire-and-forget) ──

/**
 * Trigger a chat run on an AgentScope session.
 * The actual response is delivered via the SSE subscription, not this endpoint's body.
 */
export async function triggerChat(sessionId, agentScopeId, message) {
  const userId = getUserId()
  return agentscopeClient.post('/chat/', {
    agent_id: agentScopeId,
    session_id: sessionId,
    input: {
      name: userId || 'user',
      role: 'user',
      content: [{ type: 'text', text: message }],
    },
  }, {
    headers: { 'X-User-ID': userId },
  })
}


// ── Combined: Subscribe → Trigger ──

/**
 * Complete SSE chat flow: subscribe to stream, then trigger chat.
 */
export function streamChat(sessionId, agentScopeId, message, callbacks = {}) {
  const { controller, builder } = subscribeStream(sessionId, agentScopeId, callbacks)
  triggerChat(sessionId, agentScopeId, message).catch(err => {
    if (err.name !== 'AbortError') {
      controller.abort()
      callbacks.onError?.(err)
    }
  })
  return { controller, builder }
}


// ── Agent configuration helpers ──

/** Fetch the default system prompt template. */
export async function fetchDefaultPrompt() {
  const { data } = await djangoClient.get('/ai/default-system-prompt')
  return data
}

/** Fetch the list of available platform business tools. */
export async function fetchPlatformTools() {
  const { data } = await djangoClient.get('/ai/available-tools')
  return data
}

/** Fetch the list of available workspace skills. */
export async function fetchAvailableSkills() {
  const { data } = await djangoClient.get('/ai/available-skills')
  return data
}

/** Fetch the list of knowledge base documents. */
export async function fetchKnowledgeDocuments() {
  const { data } = await djangoClient.get('/ai/knowledge/documents')
  return data
}


// ── Toolbox (shared tools / skills / extensions) ──

/** List all shared toolbox items. */
export async function fetchSharedTools() {
  const { data } = await djangoClient.get('/ai/toolbox')
  return data
}

/** Create a shared MCP tool or extension. */
export async function createSharedTool(payload) {
  const { data } = await djangoClient.post('/ai/toolbox/create', {
    name: payload.name,
    item_type: payload.item_type,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

/** Update a shared toolbox item. */
export async function updateSharedTool(itemId, payload) {
  const { data } = await djangoClient.post(`/ai/toolbox/${itemId}/update`, {
    name: payload.name,
    description: payload.description,
    config_json: payload.config_json,
  })
  return data
}

/** Delete a shared toolbox item. */
export async function deleteSharedTool(itemId) {
  const { data } = await djangoClient.post(`/ai/toolbox/${itemId}/delete`)
  return data
}

/** Import a shared toolbox item into an agent. */
export async function importFromToolbox(agentId, toolboxItemId) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/import-from-toolbox`, {
    toolbox_item_id: toolboxItemId,
  })
  return data
}

/** Upload a shared skill folder. */
export async function uploadSharedSkill(files, name) {
  const formData = new FormData()
  formData.append('name', name)
  for (const file of files) {
    formData.append('files', file, file.webkitRelativePath || file.name)
  }
  const { data } = await djangoClient.post('/ai/toolbox/upload-skill', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}


// ── MCP & Skill management ──

/** Fetch an agent's MCP servers and skills. */
export async function fetchAgentTools(agentId) {
  const { data } = await djangoClient.get(`/ai/agents/${agentId}/tools`)
  return data
}

/** Save (create or update) an MCP server config. */
export async function saveMcp(agentId, name, configJson) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/mcp/save`, {
    name,
    config_json: configJson,
  })
  return data
}

/** Test MCP server connectivity. Returns {ok, connected, detail}. */
export async function testMcpConnection(agentId, configObj) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/mcp/test`, configObj)
  return data
}

/** Upload a skill folder. files: File[], name: string */
export async function uploadSkill(agentId, files, name) {
  const formData = new FormData()
  formData.append('name', name)
  for (const file of files) {
    formData.append('files', file, file.webkitRelativePath || file.name)
  }
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/skill/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** Toggle a tool enabled/disabled. */
export async function toggleToolEnabled(agentId, toolId, enabled) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/${toolId}/toggle`, { enabled })
  return data
}

/** Delete an MCP or Skill tool. */
export async function deleteToolById(agentId, toolId) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/${toolId}/delete`)
  return data
}

// ── Agent CRUD（从 index.vue/AgentDetail.vue/ChatView.vue 裸调用收敛）──

/** 获取所有 Agent 列表 */
export async function listAgents() {
  const { data } = await djangoClient.get('/ai/agents')
  return data
}

/** 获取 Agent 健康状态 */
export async function checkAgentsHealth() {
  const { data } = await djangoClient.get('/ai/agents/health')
  return data
}

/** 测试 Agent 连接 */
export async function testAgent(agentId) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/test`)
  return data
}

/** 删除 Agent */
export async function deleteAgent(agentId) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/delete`)
  return data
}

/** 更新 Agent 模型名称 */
export async function updateAgentModel(agentId, modelName) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/update`, { model_name: modelName })
  return data
}

/** 获取 Agent 详情（编辑页） */
export async function getAgentDetail(agentId) {
  const { data } = await djangoClient.get(`/ai/agents/${agentId}`)
  return data
}

/** 检测可用模型 */
export async function detectModels(payload) {
  const { data } = await djangoClient.post('/ai/models/detect', payload)
  return data
}

/** 上传头像 — base64 JSON payload，使用默认 application/json */
export async function uploadAvatar(formData) {
  const { data } = await djangoClient.post('/ai/upload-avatar', formData)
  return data
}

/** 保存 Agent（新建或更新） */
export async function saveAgent(url, payload) {
  const { data } = await djangoClient.post(url, payload)
  return data
}

// ── 任务列表 ──

/** 获取 AI 任务列表 */
export async function listTasks(params = {}) {
  const { data } = await djangoClient.get('/ai/tasks', { params })
  return data
}

// ── 知识库（从 KnowledgeBase.vue 裸调用收敛）──

/** 获取知识库状态 */
export async function getKnowledgeStatus() {
  const { data } = await djangoClient.get('/ai/knowledge/status')
  return data
}

/** 获取知识库文档列表 */
export async function getKnowledgeDocuments() {
  const { data } = await djangoClient.get('/ai/knowledge/documents')
  return data
}

/** 重建知识库索引 */
export async function reindexKnowledge() {
  const { data } = await djangoClient.post('/ai/knowledge/reindex')
  return data
}

