<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/shared/api-client.js'
import { streamChat, SSEMessageBuilder } from './api.js'
import { Button as AnimalButton, Collapse } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import AnimatedMascot from '@/shared/components/AnimatedMascot.vue'
import { IconPlus, IconSearch, IconArrowLeft, IconSend, IconMessageCircle, IconPlay } from '@/shared/icons/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import mermaid from 'mermaid'

mermaid.initialize({
  startOnLoad: false, theme: 'base', securityLevel: 'loose',
  themeVariables: { primaryColor: '#19c8b9', primaryTextColor: '#4A3A28', lineColor: '#8a7b66', fontSize: '14px' },
})

const route = useRoute(); const router = useRouter()
const agentId = ref(parseInt(route.params.agentId))
const agent = ref(null)
const conversations = ref([])
const activeConv = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const chatBody = ref(null)

// SSE streaming state
const streamMode = ref(null)     // 'sse' | 'fallback' | null
const abortController = ref(null) // AbortController for SSE stream
const assistIdx = ref(-1)         // Index of the current assistant message being streamed
const toolCalls = ref([])         // Tool call events during streaming
const connectionMode = ref('unknown') // 'sse' | 'fallback' | 'unknown' — persistent connection state
const sseBuilder = ref(null)      // SSEMessageBuilder for current stream — tracks thinking, tool calls, etc.
const modelStatus = ref('idle')   // 'idle' | 'thinking' | 'calling_model' | 'tool_calling' | 'streaming' | 'done' — live model activity

// User confirmation state — drives the confirm dialog during SSE stream
const pendingConfirm = ref(null)  // null | { replyId, toolCalls: [...] }
const pendingConfirmMsgIdx = ref(-1) // which message index to update after confirm

// File upload
const fileInput = ref(null)
const uploading = ref(false)
const uploadedFile = ref(null)

// Conversation rename
const editingConvId = ref(null)
const editingTitle = ref('')

// Task records
const taskRecords = ref([])

// Live task cards — keyed by run_id, updated as SSE events arrive
// Each card: { run_id, title, status, device, device_model, cases, case_titles, loop_count, progress, actions }
const taskCards = ref({})

// Historical task cards — loaded from conversation API when switching chats
const taskHistory = ref([])

onMounted(() => loadAgent())
onUnmounted(() => {
  // Abort any active SSE stream when leaving the page
  if (abortController.value) abortController.value.abort()
})

const activeConvTitle = computed(() => {
  const c = conversations.value.find(c => c.id === activeConv.value)
  return c?.title || '当前对话'
})

const streamModeLabel = computed(() => {
  if (streamMode.value === 'sse') return '⚡ SSE 流式'
  if (streamMode.value === 'fallback') return '⏳ 降级模式'
  return null
})

const connectionModeLabel = computed(() => {
  if (connectionMode.value === 'sse') return 'SSE 流式通道'
  if (connectionMode.value === 'fallback') return 'Django 直连通道'
  if (connectionMode.value === 'connecting') return '发送时自动连接'
  return '检测中...'
})

const connectionModeIcon = computed(() => {
  if (connectionMode.value === 'sse') return '⚡'
  if (connectionMode.value === 'fallback') return '⏳'
  if (connectionMode.value === 'connecting') return '🔗'
  return '🔍'
})

// Live model activity status — driven by SSE onStatus callback
const modelStatusLabel = computed(() => {
  switch (modelStatus.value) {
    case 'thinking':      return '🤔 思考中'
    case 'calling_model': return '🧠 调用模型'
    case 'tool_calling':  return '🔧 调用工具'
    case 'streaming':     return '✍️ 输出中'
    case 'done':          return '✅ 已完成'
    case 'idle':          return null
    default:              return null
  }
})
const modelStatusIcon = computed(() => {
  switch (modelStatus.value) {
    case 'thinking':      return '🤔'
    case 'calling_model': return '🧠'
    case 'tool_calling':  return '🔧'
    case 'streaming':     return '✍️'
    case 'done':          return '✅'
    case 'idle':          return null
    default:              return null
  }
})

async function loadAgent() {
  try { const { data } = await client.get(`/ai/agents/${agentId.value}`); if (data.ok) { agent.value = data.agent; loadConversations(); loadTaskRecords() } } catch(_) {}
}
async function loadConversations() {
  try { const { data } = await client.get(`/ai/agents/${agentId.value}/conversations`); if (data.ok) conversations.value = data.conversations } catch(_) {}
}

// Task records
async function loadTaskRecords() {
  try {
    const { data } = await client.get('/runner/runs')
    if (data.ok && data.runs) taskRecords.value = (data.runs || []).filter(r => r.run_id?.startsWith('ai-task-')).slice(0, 10)
  } catch (_) { taskRecords.value = [] }
}

// Load AI task history for the current conversation
async function loadTaskHistory(convId) {
  if (!convId) { taskHistory.value = []; return }
  try {
    const { data } = await client.get(`/ai/conversations/${convId}/tasks`)
    if (data.ok && data.tasks) {
      taskHistory.value = data.tasks.map(t => ({
        run_id: t.run_id,
        title: t.summary || t.run_id.replace('ai-task-', '').slice(0, 8),
        status: t.status,
        device: t.device_serial,
        device_model: t.device_model || '',
        cases: t.cases || [],
        case_titles: [],
        loop_count: t.loop_count || 1,
        progress: { current: 0, total: (t.cases || []).length * (t.loop_count || 1) },
        actions: ['view_detail'],
      }))
    }
  } catch (_) { taskHistory.value = [] }
}
function goToTask(runId) { router.push('/runner') }

// File upload
function triggerUpload() { fileInput.value?.click() }
async function handleFileUpload(e) {
  const file = e.target.files?.[0]; if (!file) return
  uploading.value = true
  const formData = new FormData(); formData.append('file', file)
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/ai/upload-file', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData })
    const data = await resp.json()
    if (data.ok) { uploadedFile.value = data.data; ElMessage.success(`已解析: ${file.name} (${(data.data.size/1024).toFixed(1)}KB)`) }
    else ElMessage.error(data.error || '文件上传失败')
  } catch (e) { ElMessage.error('文件上传失败') }
  uploading.value = false; e.target.value = ''
}
function removeFile() { uploadedFile.value = null }

// Chat
async function newChat() {
  try {
    const { data } = await client.post(`/ai/agents/${agentId.value}/conversations/create`, { title: '新对话' })
    if (data.ok) {
      conversations.value.unshift({ id: data.id, title: '新对话', status: 'active', agent_scope_session_id: data.agent_scope_session_id || '' })
      connectionMode.value = data.agent_scope_session_id ? 'sse' : 'fallback'
      selectChat(data.id)
    }
  } catch(_) { connectionMode.value = 'unknown' }
}
async function selectChat(id) {
  activeConv.value = id
  try {
    const { data } = await client.get(`/ai/conversations/${id}/messages`)
    if (data.ok) {
      // Connection mode: SSE if session exists, otherwise 'connecting' (will auto-upgrade on first message)
      const conv = conversations.value.find(c => c.id === id)
      if (conv?.agent_scope_session_id) {
        connectionMode.value = 'sse'
      } else {
        // Old conversation without session — will auto-create on next sendMessage via trySSEStream
        connectionMode.value = 'connecting'
      }
      // Tag each assistant message with its flow
      messages.value = data.messages.map(m => {
        const flow = m.role === 'assistant' ? (conv?.agent_scope_session_id ? 'sse' : 'fallback') : null
        // Rebuild SSE UI state from stored blocks (跨 Turn 上下文)
        const blocks = m.blocks || []
        const textBlock = blocks.find(b => b.type === 'text')
        const thinkingBlock = blocks.find(b => b.type === 'thinking')
        const toolBlocks = blocks.filter(b => b.type === 'tool_call' || b.type === 'tool_result' || b.type === 'tool_pair')
        const hintBlock = blocks.find(b => b.type === 'hint')
        return {
          ...m,
          flow,
          content: m.content || textBlock?.text || '',
          thinking: thinkingBlock?.thinking || '',
          thinkingDone: !!(thinkingBlock?.thinking),
          toolFlow: rebuildToolFlow(toolBlocks),
          hint: _parseHintFromBlocks(hintBlock, blocks),
          reason: m.reason || 'normal',
        }
      })
    }
  } catch(_) {
    connectionMode.value = 'unknown'
  }
  // Load task history for this conversation
  loadTaskHistory(id)
  scrollBottom()
}

// Parse hint from stored blocks — handles both plain string and JSON object hints
function _parseHintFromBlocks(hintBlock, allBlocks) {
  if (!hintBlock) return ''
  const raw = hintBlock.hint || ''
  if (typeof raw === 'object') return raw
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return raw }
  }
  return raw
}

// Rebuild toolFlow array from stored ContentBlocks for cross-session display
function rebuildToolFlow(blocks) {
  if (!blocks.length) return []
  // tool_pair blocks have .call and .result
  const pairs = blocks.filter(b => b.type === 'tool_pair')
  if (pairs.length) {
    return pairs.map(p => ({
      id: p.call?.id || '',
      name: p.call?.name || '',
      displayArgs: p.call?.inputRaw || (p.call?.input ? JSON.stringify(p.call.input) : ''),
      state: p.result?.state || 'success',
      output: p.result?.output || '',
    }))
  }
  // Separate tool_call + tool_result blocks
  const calls = blocks.filter(b => b.type === 'tool_call')
  const results = blocks.filter(b => b.type === 'tool_result')
  return calls.map(c => {
    const r = results.find(r => r.id === c.id)
    return {
      id: c.id || '',
      name: c.name || '',
      displayArgs: c.inputRaw || (c.input ? JSON.stringify(c.input) : ''),
      state: r?.state || 'success',
      output: r?.output || '',
    }
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if ((!text && !uploadedFile.value) || !activeConv.value || sending.value) return
  inputText.value = ''; sending.value = true; toolCalls.value = []
  modelStatus.value = 'calling_model'  // optimistic: we just kicked off the request

  let msgText = text
  let displayText = text || ''
  if (uploadedFile.value) {
    const f = uploadedFile.value
    msgText += `\n\n[上传文件: ${f.filename} (${f.type})]\n\`\`\`\n${f.content}\n\`\`\``
    displayText = (text ? text + '\n' : '') + `📎 ${f.filename} (${(f.size/1024).toFixed(1)}KB)` + (text ? '' : '\n文件内容已发送给 AI')
    uploadedFile.value = null
  }

  // Add user message to local list (user messages don't need flow tag)
  messages.value.push({ role: 'user', content: displayText })
  assistIdx.value = messages.value.length
  // Placeholder for assistant response — flow will be set after actual delivery
  messages.value.push({ role: 'assistant', content: '', tokens: 0, flow: null })
  scrollBottom()

  // Try SSE streaming first, fall back to Django blocking mode
  try {
    await trySSEStream(msgText)
  } catch (e) {
    console.warn('SSE setup failed, falling back to Django /send:', e)
    streamMode.value = 'fallback'
    connectionMode.value = 'fallback'  // persist connection state
    // Mark this message as fallback flow
    if (assistIdx.value < messages.value.length) {
      messages.value[assistIdx.value].flow = 'fallback'
    }
    await fallbackSend(msgText)
  }
}

async function trySSEStream(msgText) {
  // Step 1: Ensure AgentScope session exists (Django backend handles agent registration + session creation)
  const { data: sessionData } = await client.post(`/ai/conversations/${activeConv.value}/create-scope-session`)
  if (!sessionData.ok) {
    throw new Error(sessionData.error || 'AgentScope session creation failed')
  }

  const sessionId = sessionData.session_id
  const agentScopeId = sessionData.agent_scope_id

  // Update conversation list so selectChat knows this is SSE next time
  const conv = conversations.value.find(c => c.id === activeConv.value)
  if (conv) conv.agent_scope_session_id = sessionId

  // Step 2: Save user message to Django
  await client.post(`/ai/conversations/${activeConv.value}/save-message`, {
    role: 'user', content: msgText,
  })

  // Step 3: Subscribe to SSE + Trigger chat
  streamMode.value = 'sse'
  connectionMode.value = 'sse'
  if (assistIdx.value < messages.value.length) {
    messages.value[assistIdx.value].flow = 'sse'
  }
  let streamDone = false
  let fullContent = ''
  let thinkingContent = ''
  // Track active tool call args being accumulated from deltas
  let currentToolName = ''
  let currentToolArgsJson = ''
  // Cache of completed toolCalls (name+args) by tool_call_id, so we can attach results
  const completedToolCalls = {}

  const { controller, builder } = streamChat(sessionId, agentScopeId, msgText, {
    // ── Live status (drives the header indicator) ──
    onStatus: (status) => {
      modelStatus.value = status
      // Auto-clear "done" after 3s so the badge doesn't linger
      if (status === 'done') {
        setTimeout(() => { if (modelStatus.value === 'done') modelStatus.value = 'idle' }, 3000)
      }
    },
    // ── Thinking process ──
    onThinkingStart: () => {
      thinkingContent = ''
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].thinking = ''
        messages.value[assistIdx.value].content = fullContent
        scrollBottom()
      }
    },
    onThinkingDelta: (delta, full) => {
      thinkingContent = full || (thinkingContent + delta)
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].thinking = thinkingContent
        scrollBottom()
      }
    },
    onThinkingEnd: (evt) => {
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].thinkingDone = true
        if (evt?.block?.thinking) {
          messages.value[assistIdx.value].thinking = evt.block.thinking
        }
        scrollBottom()
      }
    },

    // ── Text content ──
    onTextDelta: (delta, full) => {
      fullContent = full != null ? full : (fullContent + delta)
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].content = fullContent
        scrollBottom()
      }
    },
    onTextEnd: (evt) => {
      if (evt?.text != null) {
        fullContent = evt.text
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].content = fullContent
        }
      }
    },

    // ── Tool call (ReAct loop) — name from START, args from DELTAs, completed at END ──
    onToolCallStart: (evt) => {
      currentToolName = evt.name
      currentToolArgsJson = ''
      toolCalls.value.push({ id: evt.toolCallId, name: evt.name, state: 'calling' })
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
        scrollBottom()
      }
    },
    onToolCallDelta: (evt) => {
      currentToolArgsJson = evt.argsJson != null ? evt.argsJson : (currentToolArgsJson + (evt.delta || ''))
    },
    onToolCallEnd: (evt) => {
      // evt.toolCall has the reconstructed { id, name, input, inputRaw, state: 'submitted' }
      const tc = evt.toolCall
      if (tc) {
        completedToolCalls[tc.id] = tc
        const idx = toolCalls.value.findIndex(t => t.id === tc.id)
        const displayArgs = tc.inputRaw || currentToolArgsJson
        if (idx >= 0) {
          toolCalls.value[idx] = { ...tc, state: 'submitted', displayArgs }
        }
      }
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
        scrollBottom()
      }
    },

    // ── Tool result — output streamed via TEXT_DELTA, finalized at END ──
    onToolResultStart: (evt) => {
      const idx = toolCalls.value.findIndex(t => t.id === evt.toolCallId)
      if (idx >= 0) toolCalls.value[idx].state = 'running'
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
        scrollBottom()
      }
    },
    onToolResultDelta: (evt) => {
      const idx = toolCalls.value.findIndex(t => t.id === evt.toolCallId)
      if (idx >= 0) {
        toolCalls.value[idx].partialOutput = evt.output != null ? evt.output : ((toolCalls.value[idx].partialOutput || '') + (evt.delta || ''))
      }
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
        scrollBottom()
      }
    },
    onToolResultEnd: (evt) => {
      // evt.toolResult = { id, name, output, state }
      const tr = evt.toolResult
      if (tr) {
        const idx = toolCalls.value.findIndex(t => t.id === tr.id)
        if (idx >= 0) {
          toolCalls.value[idx].state = tr.state || 'success'
          toolCalls.value[idx].output = tr.output
          toolCalls.value[idx].partialOutput = null
        }
        // Auto-update task card progress when run_test completes
        _updateTaskCardProgress(tr)
      }
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].toolFlow = [...toolCalls.value]
        scrollBottom()
      }
    },

    // ── Model call info ──
    onModelCallStart: (evt) => {
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].modelName = evt.modelName
      }
    },
    onModelCallEnd: (evt) => {
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].tokens = evt.outputTokens || 0
        messages.value[assistIdx.value].inputTokens = evt.inputTokens || 0
      }
    },

    // ── Hint — parse task cards and store for live updates ──
    onHint: (evt) => {
      let hintData = evt.hint
      if (typeof hintData === 'string') {
        try { hintData = JSON.parse(hintData) } catch {}
      }
      if (hintData?.type === 'task_card' && hintData?.run_id) {
        // Merge with existing card (preserve live progress)
        const existing = taskCards.value[hintData.run_id] || {}
        taskCards.value[hintData.run_id] = { ...existing, ...hintData, updatedAt: Date.now() }
        // Store parsed card as hint for rendering
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].hint = hintData  // parsed object → triggers task-card rendering
        }
        scrollBottom()
      } else {
        // Plain text hint (e.g. plan steps)
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].hint = hintData
          scrollBottom()
        }
      }
    },

    // ── User confirmation (P0 — dangerous tool calls require approval) ──
    // When AgentScope emits REQUIRE_USER_CONFIRM, pause display and prompt the user.
    // The stream continues but we hold off rendering pending tool calls until confirmed.
    onRequireConfirm: (evt) => {
      // evt = { toolCalls: [{tool_call_id, tool_call_name, arguments}] }
      modelStatus.value = 'idle'  // pause the status indicator
      pendingConfirm.value = evt
      pendingConfirmMsgIdx.value = assistIdx.value
    },

    // ── Exceed max iterations — more visible display ──
    onExceedMaxIters: (evt) => {
      if (assistIdx.value < messages.value.length) {
        const block = builder.getFullThinking()
        messages.value[assistIdx.value].thinking = block
        messages.value[assistIdx.value].thinkingDone = true
        messages.value[assistIdx.value].reason = 'exceed_max_iters'
        // Show a prominent warning banner instead of inline text
        messages.value[assistIdx.value].content =
          (messages.value[assistIdx.value].content || '') +
          '\n\n⚠️ **[智能体已达最大推理次数]** 响应可能被截断，建议简化问题或分步提问。'
        scrollBottom()
      }
    },

    // ── Stream lifecycle ──
    onDone: async () => {
      if (streamDone) return
      streamDone = true
      const finalContent = builder.getFullText() || fullContent
      const blocks = builder.getBlocks()
      const reason = builder.getReason()
      try {
        await client.post(`/ai/conversations/${activeConv.value}/save-message`, {
          role: 'assistant',
          content: finalContent,
          blocks,
          reason,
          tokens: builder.getTokenUsage().total || 0,
          input_tokens: builder.getTokenUsage().input || 0,
          model_name: builder.modelName || '',
        })
        loadConversations()
        await nextTick()
        renderMermaidBlocks()
      } catch (e) {
        console.error('Failed to save streamed message:', e)
      }
      sending.value = false
      streamMode.value = null
      abortController.value = null
      scrollBottom()
    },
    onError: async (err) => {
      if (streamDone) return
      streamDone = true
      console.warn('SSE stream error, falling back:', err)
      streamMode.value = 'fallback'
      connectionMode.value = 'fallback'
      modelStatus.value = 'idle'
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].flow = 'fallback'
      }
      await fallbackSend(msgText)
    },
  })

  abortController.value = controller
  sseBuilder.value = builder

  // Update conversation title from first user message
  try {
    const conv = conversations.value.find(c => c.id === activeConv.value)
    if (conv && conv.title === '新对话') {
      const { data } = await client.post(`/ai/conversations/${activeConv.value}/rename`, { title: msgText.slice(0, 30) })
      if (data.ok) conv.title = data.title
    }
  } catch (_) {}
}

async function fallbackSend(msgText) {
  // Django blocking mode — already saves both messages
  try {
    const { data } = await client.post(`/ai/conversations/${activeConv.value}/send`, { message: msgText })
    if (data.ok) {
      // Replace our placeholder with the actual response from Django
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value] = { ...data.message, flow: 'fallback' }
      }
      loadConversations()
      await nextTick()
      renderMermaidBlocks()
    } else {
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value] = { role: 'assistant', content: data.error || '发送失败', tokens: 0, flow: 'fallback' }
      }
    }
  } catch (e) {
    console.error('Fallback send failed:', e)
    const errMsg = e.code === 'ECONNABORTED' ? '请求超时，请重试' : (e.response?.status === 500 ? '服务器错误' : '发送失败，请检查服务状态。')
    if (assistIdx.value < messages.value.length) {
      messages.value[assistIdx.value] = { role: 'assistant', content: errMsg, tokens: 0, flow: 'fallback' }
    }
  }
  sending.value = false
  streamMode.value = null
  abortController.value = null
  scrollBottom()
}

function stopStream() {
  if (abortController.value) {
    abortController.value.abort()
    // Mark as stopped before saving so the reason is persisted
    if (assistIdx.value < messages.value.length && messages.value[assistIdx.value].flow === 'sse') {
      const partial = messages.value[assistIdx.value].content
      client.post(`/ai/conversations/${activeConv.value}/save-message`, {
        role: 'assistant',
        content: partial || '（用户主动停止）',
        tokens: 0,
        reason: 'stopped',
        blocks: sseBuilder.value ? sseBuilder.value.getBlocks() : [],
      }).catch(e => console.error('Failed to save partial stream:', e))
    }
    sending.value = false
    abortController.value = null
    streamMode.value = null
    modelStatus.value = 'idle'
    scrollBottom()
  }
  // Also cancel any pending confirmation
  pendingConfirm.value = null
}

// User confirmation — approve or deny a dangerous tool call
async function resolveConfirm(toolCallId, approved, reason = '') {
  const confirm = pendingConfirm.value
  if (!confirm) return
  // Mark the tool call in the UI as approved/denied
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
  modelStatus.value = 'tool_calling'  // resume indicator

  // Send result back to AgentScope via Django backend
  const result = {
    reply_id: confirm.replyId || '',
    confirm_results: [{
      tool_call_id: toolCallId,
      approved,
      ...(reason ? { reason } : {}),
    }],
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
  for (const tc of confirm.toolCalls) {
    await resolveConfirm(tc.tool_call_id, true)
  }
}

async function denyAll() {
  const confirm = pendingConfirm.value
  if (!confirm?.toolCalls) return
  for (const tc of confirm.toolCalls) {
    await resolveConfirm(tc.tool_call_id, false, '用户拒绝')
  }
}

function scrollBottom() { nextTick(() => { if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight }) }
function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }

// Conversation rename
function startRename(conv) {
  editingConvId.value = conv.id; editingTitle.value = conv.title
  nextTick(() => { const input = document.querySelector('.conv-rename-input'); if (input) { input.focus(); input.select() } })
}
async function finishRename() {
  const id = editingConvId.value; const title = editingTitle.value.trim()
  editingConvId.value = null
  if (!title || !id) return
  try { const { data } = await client.post(`/ai/conversations/${id}/rename`, { title }); if (data.ok) { const c = conversations.value.find(x => x.id === id); if (c) c.title = data.title } } catch (_) {}
}
function cancelRename() { editingConvId.value = null }

async function deleteConversation(conv) {
  try {
    await ElMessageBox.confirm(`删除对话「${conv.title}」？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    const { data } = await client.post(`/ai/conversations/${conv.id}/delete`)
    if (data.ok) { ElMessage.success('已删除'); if (activeConv.value === conv.id) { activeConv.value = null; messages.value = [] }; loadConversations() }
  } catch (_) {}
}

// Avatars
function avatarStyle(avatar) { return avatar?.startsWith('/api/ai/avatars/') ? { backgroundImage: `url(${avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' } : {} }
function avatarText(avatar) { return avatar?.startsWith('/api/ai/avatars/') ? '' : (avatar || '') }

// Markdown
function renderMarkdown(text) { if (!text) return ''; pendingMermaidBlocks = []; return marked(text, { breaks: true, gfm: true }) }

function toggleThinking(m) {
  m.thinkingExpanded = !m.thinkingExpanded
}

function toolStateLabel(state) {
  const labels = { calling: '调用中...', submitted: '参数已提交', running: '执行中...', success: '执行完成', error: '执行出错', finished: '已完成', denied: '已拒绝' }
  return labels[state] || state || ''
}

// Format tool arguments for the confirm dialog — makes JSON readable
function formatConfirmArgs(args) {
  if (!args) return ''
  if (typeof args === 'string') {
    try { return JSON.stringify(JSON.parse(args), null, 2) } catch { return args }
  }
  return JSON.stringify(args, null, 2)
}

// Parse run_test output to extract case-by-case results → update task card progress
function _parseTaskCardProgress(output) {
  if (!output) return null
  const str = typeof output === 'string' ? output : JSON.stringify(output)
  // Match patterns like "passed=X" or "通过=X" or "X/Y passed"
  const passedMatch = str.match(/(?:passed|通过)[=:]?\s*(\d+)/i)
  const failedMatch = str.match(/(?:failed|失败)[=:]?\s*(\d+)/i)
  const totalMatch = str.match(/Total:\s*(\d+)/i)
  if (!passedMatch && !failedMatch) return null
  const passed = parseInt(passedMatch?.[1] || '0')
  const failed = parseInt(failedMatch?.[1] || '0')
  const total = parseInt(totalMatch?.[1] || (passed + failed))
  return { passed, failed, total }
}

// Update task card state when a relevant tool call completes
function _updateTaskCardProgress(tr) {
  const name = tr?.name || ''
  const output = tr?.output || ''
  const state = tr?.state || ''
  // Find any task card that should be updated
  for (const [runId, card] of Object.entries(taskCards.value)) {
    if (name === 'create_runner_task') {
      taskCards.value[runId] = { ...card, status: 'PENDING', updatedAt: Date.now() }
    } else if (name === 'run_test') {
      const parsed = _parseTaskCardProgress(output)
      const isDone = state === 'success' || state === 'finished'
      const status = isDone ? (parsed?.failed > 0 ? 'FAILED' : 'COMPLETED') : 'RUNNING'
      const progress = parsed ? { current: parsed.total, total: parsed.total } : card.progress
      taskCards.value[runId] = { ...card, status, progress, updatedAt: Date.now() }
      // Also update in message hints
      for (const m of messages.value) {
        if (m.hint?.run_id === runId) m.hint = { ...card, status, progress }
      }
    } else if (name === 'stop_run') {
      taskCards.value[runId] = { ...card, status: 'STOPPED', updatedAt: Date.now() }
    }
  }
}

// Open task detail page
function viewTaskDetail(runId) { router.push(`/runner?run=${runId}`) }

// Stop a running task — call backend then update card status
async function stopTask(runId) {
  if (taskCards.value[runId]) {
    taskCards.value[runId] = { ...taskCards.value[runId], status: 'STOPPED', updatedAt: Date.now() }
  }
  try {
    await client.post(`/runner/run/${runId}/stop`)
    ElMessage.success('任务已停止')
  } catch (e) {
    ElMessage.error('停止任务失败')
  }
}

// Compute CSS class for task status badge
function taskStatusClass(status) {
  return status?.toLowerCase() || ''
}
function taskStatusLabel(status) {
  const map = { PENDING: '待执行', RUNNING: '执行中', COMPLETED: '已完成', FAILED: '失败', STOPPED: '已停止' }
  return map[status?.toUpperCase()] || status || ''
}
function progressPercent(progress) {
  if (!progress) return 0
  const p = progress.current / progress.total
  return Math.round(Math.max(0, Math.min(100, p * 100)))
}
let mermaidId = 0; let pendingMermaidBlocks = []
const mermaidRenderer = {
  code(code, lang) {
    if (lang === 'mermaid') {
      const id = `mm-${++mermaidId}`
      const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      pendingMermaidBlocks.push({ id, code })
      return `<div class="mermaid-placeholder" data-mm-id="${id}"><pre><code class="language-mermaid">${escaped}</code></pre></div>`
    }
    const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    return `<pre><code class="language-${lang || ''}">${escaped}</code></pre>`
  },
}
marked.use({ renderer: mermaidRenderer })

async function renderMermaidBlocks() {
  if (!pendingMermaidBlocks.length) return
  const jobs = pendingMermaidBlocks.splice(0)
  await nextTick(); await new Promise(r => requestAnimationFrame(r))
  for (const { id, code } of jobs) {
    const placeholder = document.querySelector(`[data-mm-id="${id}"]`); if (!placeholder) continue
    try {
      const { svg } = await mermaid.render(id, code)
      const wrapper = document.createElement('div'); wrapper.className = 'mermaid-diagram'; wrapper.innerHTML = svg
      placeholder.replaceWith(wrapper)
    } catch (e) { placeholder.classList.remove('mermaid-placeholder'); placeholder.removeAttribute('data-mm-id') }
  }
}
</script>

<template>
  <div class="doc-page chat-page">
    <PageHeader :title="agent ? `${agent.name} · 对话` : 'AI 对话'" :subtitle="agent?.description || '与智能体进行多轮对话，支持 Markdown、Mermaid 图表与文件上传'" color="app-yellow" />

    <div class="doc-body">
      <div class="chat-layout">
        <!-- Left: conversation sidebar -->
        <section class="doc-section chat-sidebar">
          <button class="back-btn" @click="router.push('/ai-assistant')"><IconArrowLeft :size="18" /><span>返回智能体列表</span></button>
          <button class="new-chat-btn" @click="newChat"><IconPlus :size="18" /><span>开启新对话</span></button>

          <!-- Agent card -->
          <div class="agent-card" v-if="agent">
            <div class="agent-avatar" :style="avatarStyle(agent.avatar)">
              <span v-if="avatarText(agent.avatar)">{{ avatarText(agent.avatar) }}</span>
                          </div>
            <div class="agent-info"><div class="agent-name">{{ agent.name }}</div><div class="agent-provider">{{ agent.model_provider }} / {{ agent.model_name }}</div></div>
          </div>

          <!-- Conversation list -->
          <div class="conv-list">
            <div class="conv-list-title"><IconMessageCircle :size="15" /><span>对话历史</span><span class="conv-count">{{ conversations.length }}</span></div>
            <div v-for="c in conversations" :key="c.id" :class="['conv-item', { active: activeConv === c.id }]" @click="selectChat(c.id)">
              <span class="conv-indicator" :class="{ active: activeConv === c.id }" />
              <span v-if="editingConvId === c.id" class="conv-title" @click.stop>
                <input class="conv-rename-input" v-model="editingTitle" @keydown.enter="finishRename" @keydown.escape="cancelRename" @blur="finishRename" />
              </span>
              <span v-else class="conv-title" @dblclick.stop="startRename(c)" :title="'双击修改名称'">{{ c.title }}</span>
              <span class="conv-status" :class="c.status" />
              <button class="conv-delete-btn" @click.stop="deleteConversation(c)" title="删除对话">✕</button>
            </div>
            <div v-if="!conversations.length" class="conv-empty"><IconSearch :size="36" /><span>暂无对话记录</span><span class="conv-empty-hint">点击上方「开启新对话」</span></div>
          </div>

          <!-- Task cards — live SSE cards + history -->
          <div class="task-records">
            <Collapse question="📋 AI 任务卡片" :default-expanded="false">
              <!-- Live task cards (from SSE) -->
              <div v-if="Object.keys(taskCards).length" class="task-records-section">
                <div class="task-section-title">实时</div>
                <div v-for="(card, rid) in taskCards" :key="rid" class="task-record-item task-card-item"
                     :class="card.status?.toLowerCase()" @click="viewTaskDetail(rid)">
                  <span class="task-record-status" :class="card.status?.toLowerCase()"></span>
                  <div class="task-record-info">
                    <span class="task-record-name">{{ card.title || rid }}</span>
                    <span class="task-record-meta">{{ card.device || '' }} · {{ (card.case_titles || []).length }} 用例</span>
                  </div>
                  <span class="task-record-badge" :class="card.status?.toLowerCase()">{{ taskStatusLabel(card.status) }}</span>
                </div>
              </div>
              <!-- Historical tasks from API -->
              <div v-if="taskHistory.length" class="task-records-section">
                <div v-if="Object.keys(taskCards).length" class="task-section-title">历史</div>
                <div v-for="t in taskHistory" :key="t.run_id" class="task-record-item"
                     :class="t.status?.toLowerCase()" @click="viewTaskDetail(t.run_id)">
                  <span class="task-record-status" :class="t.status?.toLowerCase()"></span>
                  <div class="task-record-info"><span class="task-record-name">{{ t.title || t.run_id.replace('ai-task-','').slice(0,12) }}</span><span class="task-record-meta">{{ t.device || '' }} · {{ (t.cases||[]).length }} 用例</span></div>
                  <IconPlay :size="14" />
                </div>
              </div>
              <div v-if="!Object.keys(taskCards).length && !taskHistory.length" class="task-records-empty">
                暂无任务卡片
              </div>
            </Collapse>
          </div>
        </section>

        <!-- Right: chat area -->
        <section class="doc-section chat-main">
          <div v-if="!activeConv" class="chat-empty">
            <div class="empty-avatar"><AnimatedMascot :size="72" /></div>
            <p class="empty-title">开始一场对话</p>
            <p class="empty-desc">在左侧选择已有对话，或点击「开启新对话」创建新会话</p>
          </div>

          <template v-else>
            <div class="chat-header">
              <div class="chat-header-left">
                <IconMessageCircle :size="20" :color="'#19c8b9'" />
                <span class="chat-header-title">{{ activeConvTitle }}</span>
                <span v-if="streamModeLabel" class="stream-mode-badge" :class="streamMode">{{ streamModeLabel }}</span>
                <span v-if="modelStatusLabel" class="model-status-badge" :class="modelStatus">
                  <span class="model-status-dot"></span>{{ modelStatusLabel }}
                </span>
              </div>
              <div class="chat-header-right">
                <span class="connection-indicator" :class="connectionMode" :title="connectionModeLabel">{{ connectionModeIcon }} {{ connectionModeLabel }}</span>
                <span class="msg-count">{{ messages.length }} 条消息</span>
                <button v-if="sending && streamMode === 'sse'" class="stop-btn" @click="stopStream" title="停止生成">⏹ 停止</button>
              </div>
            </div>

            <div ref="chatBody" class="chat-body">
              <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
                <div class="msg-avatar" :style="avatarStyle(m.role === 'assistant' ? agent?.avatar : '')">
                  <span v-if="m.role === 'user'">👤</span>
                  <template v-else><span v-if="avatarText(agent?.avatar)">{{ avatarText(agent?.avatar) }}</span></template>
                </div>
                <div class="msg-content">
                  <div class="msg-author">{{ m.role === 'user' ? '我' : agent?.name || 'AI' }}<span v-if="m.role === 'assistant' && m.flow" class="msg-flow-tag" :class="m.flow">{{ m.flow === 'sse' ? '⚡ SSE' : '⏳ Django' }}</span></div>
                  <!-- Thinking process (collapsible, only for SSE messages) -->
                  <div v-if="m.role === 'assistant' && m.thinking" class="thinking-block" :class="{ 'thinking-done': m.thinkingDone }">
                    <div class="thinking-header" @click="toggleThinking(m)">
                      <span class="thinking-icon">{{ m.thinkingDone ? '💭' : '🤔' }}</span>
                      <span class="thinking-label">思考过程</span>
                      <span class="thinking-toggle">{{ m.thinkingExpanded ? '收起' : '展开' }}</span>
                    </div>
                    <div v-if="m.thinkingExpanded || !m.thinkingDone" class="thinking-body" v-html="m.thinking"></div>
                  </div>
                  <!-- Tool call flow (only for SSE messages) -->
                  <div v-if="m.role === 'assistant' && m.toolFlow && m.toolFlow.length" class="tool-flow-block">
                    <div v-for="tc in m.toolFlow" :key="tc.id" class="tool-step" :class="tc.state">
                      <div class="tool-step-header">
                        <span class="tool-step-icon">{{ tc.state === 'calling' ? '⏳' : tc.state === 'running' ? '🔄' : tc.state === 'success' ? '✅' : tc.state === 'error' ? '❌' : '🔧' }}</span>
                        <span class="tool-step-name">{{ tc.name }}</span>
                        <span class="tool-step-state">{{ toolStateLabel(tc.state) }}</span>
                      </div>
                      <div v-if="tc.displayArgs" class="tool-step-args">
                        <details><summary>参数</summary><pre>{{ tc.displayArgs }}</pre></details>
                      </div>
                      <div v-if="tc.partialOutput" class="tool-step-output streaming">
                        <span class="tool-streaming-dot"></span> {{ tc.partialOutput.slice(0, 200) }}...
                      </div>
                      <div v-if="tc.output && !tc.partialOutput" class="tool-step-output">
                        {{ typeof tc.output === 'string' ? tc.output.slice(0, 300) : JSON.stringify(tc.output).slice(0, 300) }}
                      </div>
                    </div>
                  </div>
                  <!-- Hint block — task card OR plain hint text -->
                  <template v-if="m.role === 'assistant' && m.hint">
                    <!-- Task card: rendered when m.hint is an object with type === 'task_card' -->
                    <div v-if="m.hint && m.hint.type === 'task_card'" class="task-card">
                      <div class="task-card-header">
                        <span class="task-status-badge" :class="taskStatusClass(m.hint.status)">{{ taskStatusLabel(m.hint.status) }}</span>
                        <span class="task-id">#{{ m.hint.run_id?.replace('ai-task-','').slice(0,12) }}</span>
                      </div>
                      <div class="task-title">{{ m.hint.title || 'AI 任务' }}</div>
                      <div class="task-meta">
                        <span>📱 {{ m.hint.device || '—' }}</span>
                        <span v-if="m.hint.device_model"> ({{ m.hint.device_model }})</span>
                      </div>
                      <div class="task-meta">
                        <span>📋 {{ (m.hint.case_titles || []).length }} 个用例</span>
                        <span v-if="m.hint.loop_count > 1"> · 🔁 {{ m.hint.loop_count }} 轮</span>
                      </div>
                    </div>
                    <!-- SOP card: rendered when m.hint.type === 'sop_card' -->
                    <div v-else-if="m.hint && m.hint.type === 'sop_card'" class="sop-card">
                      <div class="sop-card-header">
                        <span class="sop-icon">📋</span>
                        <span class="sop-title">SOP 工作流</span>
                        <span class="sop-phase-badge" :class="'phase-' + m.hint.phase">
                          阶段 {{ m.hint.phase }}: {{ m.hint.phase_label }}
                        </span>
                      </div>
                      <div class="sop-requirement" v-if="m.hint.requirement">
                        <strong>需求:</strong> {{ m.hint.requirement }}
                      </div>
                      <div class="sop-cases" v-if="m.hint.case_count > 0">
                        <strong>用例设计 ({{ m.hint.case_count }} 个):</strong>
                        <ol>
                          <li v-for="(name, i) in m.hint.case_names" :key="i">{{ name }}</li>
                        </ol>
                      </div>
                      <div class="sop-hint" v-if="m.hint.next_hint">
                        <span class="arrow">→</span> {{ m.hint.next_hint }}
                      </div>
                    </div>
                    <!-- Generic hint: rendered as plain text hint block -->
                    <div v-else class="hint-block">
                      <span class="hint-icon">💡</span>
                      <span class="hint-text">{{ typeof m.hint === 'string' ? m.hint : (m.hint.hint || m.hint.text || JSON.stringify(m.hint)) }}</span>
                    </div>
                  </template>
                  <!-- Main text content -->
                  <div class="msg-text" v-html="m.role === 'user' ? m.content : renderMarkdown(m.content)"></div>
                  <!-- Token usage -->
                  <div v-if="m.tokens" class="msg-tokens">
                    <span v-if="m.model_name" class="model-name-tag">{{ m.model_name }}</span>
                    {{ m.tokens }} tokens
                    <span v-if="m.inputTokens" style="color: #8a7b66; font-size: 11px;">(输入 {{ m.inputTokens }} / 输出 {{ m.tokens - m.inputTokens || m.tokens }})</span>
                  </div>
                  <!-- End reason badge (non-normal) -->
                  <div v-if="m.role === 'assistant' && m.reason && m.reason !== 'normal'" class="reason-badge" :class="m.reason">
                    <span v-if="m.reason === 'exceed_max_iters'">⚠️ 达到最大迭代次数</span>
                    <span v-else-if="m.reason === 'stopped'">⏹ 用户主动停止</span>
                    <span v-else-if="m.reason === 'error'">❌ 异常终止</span>
                    <span v-else>{{ m.reason }}</span>
                  </div>
                </div>
              </div>
              <div v-if="sending && !messages[messages.length-1]?.content" class="msg assistant">
                <div class="msg-avatar"><span v-if="avatarText(agent?.avatar)">{{ avatarText(agent?.avatar) }}</span></div>
                <div class="msg-content"><div class="msg-author">{{ agent?.name || 'AI' }}</div><div class="msg-text typing"><span></span><span></span><span></span></div></div>
              </div>
            </div>

            <!-- User confirmation dialog — shown when LLM emits REQUIRE_USER_CONFIRM (P0 security) -->
            <div v-if="pendingConfirm" class="confirm-overlay">
              <div class="confirm-dialog">
                <div class="confirm-header">
                  <span class="confirm-icon">⚠️</span>
                  <span class="confirm-title">操作需要确认</span>
                </div>
                <div class="confirm-body">
                  <p class="confirm-desc">AI 助手请求执行以下敏感操作：</p>
                  <div class="confirm-tools">
                    <div v-for="tc in (pendingConfirm.toolCalls || [])" :key="tc.tool_call_id" class="confirm-tool-item">
                      <span class="confirm-tool-icon">🔧</span>
                      <div class="confirm-tool-info">
                        <span class="confirm-tool-name">{{ tc.tool_call_name }}</span>
                        <pre class="confirm-tool-args">{{ formatConfirmArgs(tc.arguments) }}</pre>
                      </div>
                      <div class="confirm-tool-actions">
                        <button class="confirm-btn approve" @click="resolveConfirm(tc.tool_call_id, true)">✅ 允许</button>
                        <button class="confirm-btn deny" @click="resolveConfirm(tc.tool_call_id, false)">❌ 拒绝</button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="confirm-footer">
                  <button class="confirm-btn approve-all" @click="approveAll">✅ 全部允许</button>
                  <button class="confirm-btn deny-all" @click="denyAll">❌ 全部拒绝</button>
                  <button class="confirm-btn cancel" @click="pendingConfirm = null">取消</button>
                </div>
              </div>
            </div>

            <!-- File preview -->
            <div v-if="uploadedFile" class="file-preview">
              <span class="file-preview-icon">📎</span><span class="file-preview-name">{{ uploadedFile.filename }}</span><span class="file-preview-size">({{ (uploadedFile.size/1024).toFixed(1) }} KB)</span>
              <button class="file-preview-remove" @click="removeFile">✕</button>
            </div>

            <div class="chat-input">
              <input ref="fileInput" type="file" accept=".txt,.log,.md,.json,.xml,.csv,.py,.js,.html,.css,.yaml,.yml,.docx,.xlsx,.pdf" @change="handleFileUpload" style="display:none" />
              <button class="upload-btn" @click="triggerUpload" :disabled="sending" title="上传文件 (txt/log/md/docx/xlsx/pdf 等)">📎</button>
              <div class="input-box">
                <el-input v-model="inputText" type="textarea" :rows="3" placeholder="输入消息，Enter 发送，Shift+Enter 换行..." @keydown="handleKey" :disabled="sending" resize="none" />
              </div>
              <button class="send-btn" @click="sendMessage" :disabled="(!inputText.trim() && !uploadedFile) || sending"><IconSend :size="20" /><span>{{ sending ? '发送中' : '发送' }}</span></button>
            </div>
          </template>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.chat-page :deep(.doc-body) { flex: 1; min-height: 0; overflow: hidden; }
.chat-layout { flex: 1; display: grid; grid-template-columns: 300px 1fr; gap: 20px; min-height: 0; height: 100%; }

/* Sidebar */
.chat-sidebar { display: flex; flex-direction: column; padding: 16px; overflow: hidden; min-height: 0; gap: 12px; height: 100%; }
.back-btn { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 12px 16px; border: 2px solid #19c8b9; border-radius: 12px; background: #e6f9f6; color: #158a80; font-size: 15px; font-weight: 700; font-family: inherit; cursor: pointer; transition: all 0.2s ease; flex-shrink: 0; }
.back-btn:hover { background: #19c8b9; color: #fff; box-shadow: 0 4px 14px rgba(25,200,185,0.35); transform: translateY(-1px); }
.new-chat-btn { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 12px 16px; border: none; border-radius: 12px; background: linear-gradient(135deg, #f7a8c4 0%, #e88a5f 100%); color: #fff; font-size: 15px; font-weight: 700; font-family: inherit; cursor: pointer; transition: all 0.2s ease; flex-shrink: 0; box-shadow: 0 3px 10px rgba(232,138,95,0.3); }
.new-chat-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(232,138,95,0.45); }

.agent-card { display: flex; align-items: center; gap: 12px; padding: 14px; border-radius: 12px; background: linear-gradient(135deg, #faf9f4 0%, #f5f3ed 100%); border: 1px solid #e8e2d6; flex-shrink: 0; }
.agent-avatar { width: 48px; height: 48px; border-radius: 12px; background: rgba(139,115,85,0.08); display: flex; align-items: center; justify-content: center; font-size: 26px; flex-shrink: 0; overflow: hidden; }
.agent-name { font-size: 16px; font-weight: 700; color: #4A3A28; line-height: 1.3; }
.agent-provider { font-size: 12px; color: #988B7A; margin-top: 3px; }

.conv-list { flex: 1; overflow-y: auto; padding: 4px 0; display: flex; flex-direction: column; gap: 6px; min-height: 0; }
.conv-list-title { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; color: #a0936e; text-transform: uppercase; letter-spacing: 0.5px; padding: 8px 6px 6px; border-bottom: 1px solid #f0ebe0; margin-bottom: 4px; }
.conv-count { font-size: 12px; padding: 1px 8px; border-radius: 10px; background: #f0e8d8; color: #8a7b66; font-weight: 700; }

.conv-item { display: flex; align-items: center; gap: 10px; padding: 13px 14px; border-radius: 10px; cursor: pointer; font-size: 15px; color: #5c4b38; transition: all 0.18s ease; border: 1px solid transparent; }
.conv-item:hover { background: #f5f3ed; border-color: #e8e2d6; }
.conv-item.active { background: #e6f9f6; border-color: #19c8b9; color: #158a80; font-weight: 700; box-shadow: 0 2px 8px rgba(25,200,185,0.12); }
.conv-indicator { width: 4px; height: 24px; border-radius: 4px; background: #d0c8b8; flex-shrink: 0; transition: all 0.18s ease; }
.conv-indicator.active { background: #19c8b9; height: 32px; box-shadow: 0 0 8px rgba(25,200,185,0.4); }
.conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: default; }
.conv-rename-input { width: 100%; border: 1.5px solid #19c8b9; border-radius: 6px; padding: 4px 8px; font-size: 14px; font-family: inherit; color: #4A3A28; background: #fff; outline: none; }
.conv-delete-btn { display: none; align-items: center; justify-content: center; width: 22px; height: 22px; border: none; border-radius: 6px; background: none; color: #c4b89e; font-size: 12px; cursor: pointer; flex-shrink: 0; transition: all 0.15s; }
.conv-item:hover .conv-delete-btn { display: flex; }
.conv-delete-btn:hover { background: rgba(232,95,95,0.12); color: #e85f5f; }
.conv-status { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.conv-status.active { background: #6fba2c; }
.conv-status.paused { background: #e8a735; }
.conv-status.error { background: #e85f5f; }
.conv-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 40px 16px; color: #a0936e; font-size: 14px; text-align: center; }
.conv-empty-hint { font-size: 12px; color: #c4b89e; }

/* Task records */
.task-records { margin-top: 12px; flex-shrink: 0; }
.task-records :deep(.animal-collapse__question) { font-size: 13px; font-weight: 700; color: #6b5b48; }
.task-records-section { margin-bottom: 4px; }
.task-section-title { font-size: 11px; color: #9CA3AF; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 4px 6px 2px; }
.task-records-list { display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; }
.task-record-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: background 0.15s; font-size: 12px; }
.task-record-item:hover { background: rgba(25,200,185,0.06); }
.task-record-item.task-card-item { border-left: 3px solid #534AB7; }
.task-record-item.running { border-left-color: #F59E0B; }
.task-record-item.pending { border-left-color: #6366F1; }
.task-record-item.completed { border-left-color: #10B981; }
.task-record-item.failed { border-left-color: #EF4444; }
.task-record-item.stopped { border-left-color: #9CA3AF; }
.task-record-status { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.task-record-status.running { background: #409eff; animation: pulse-dot 1.5s infinite; }
.task-record-status.pending { background: #e6a23c; }
.task-record-status.completed { background: #6fba2c; }
.task-record-status.failed { background: #e85f5f; }
.task-record-status.stopped { background: #9CA3AF; }
.task-record-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 6px; font-weight: 700; flex-shrink: 0;
}
.task-record-badge.running   { background: #FEF3C7; color: #92400E; }
.task-record-badge.pending   { background: #EEF2FF; color: #4F46E5; }
.task-record-badge.completed { background: #D1FAE5; color: #065F46; }
.task-record-badge.failed    { background: #FEE2E2; color: #991B1B; }
.task-record-badge.stopped   { background: #F3F4F6; color: #374151; }
.task-record-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.task-record-name { font-weight: 600; color: #4A3A28; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-record-meta { font-size: 10px; color: #a0936e; }
.task-records-empty { font-size: 12px; color: #9CA3AF; padding: 8px 6px; text-align: center; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* Chat main */
.chat-main { display: flex; flex-direction: column; padding: 0; min-height: 0; overflow: hidden; height: 100%; }
.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; color: #988B7A; padding: 40px; }
.empty-avatar { padding: 24px; background: #faf9f4; border-radius: 28px; border: 2px dashed #d8cfc0; }
.empty-title { font-size: 20px; font-weight: 700; color: #4A3A28; }
.empty-desc { font-size: 15px; color: #988B7A; }

.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; background: #fff; border-bottom: 2px solid #e8e2d6; flex-shrink: 0; }
.chat-header-left { display: flex; align-items: center; gap: 10px; }
.chat-header-title { font-size: 16px; font-weight: 700; color: #4A3A28; }
.msg-count { font-size: 13px; color: #a0936e; padding: 3px 10px; background: #f5f3ed; border-radius: 10px; font-weight: 600; }

/* Stream mode badge */
.stream-mode-badge { font-size: 12px; padding: 3px 10px; border-radius: 8px; font-weight: 700; }
.stream-mode-badge.sse { background: #e6f9f6; color: #158a80; border: 1px solid #19c8b9; animation: pulse-badge 1.5s infinite; }
.stream-mode-badge.fallback { background: #fef6e6; color: #8a6d14; border: 1px solid #e8a735; }
@keyframes pulse-badge { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

/* Model status badge — shows live model activity (thinking / calling / streaming / done) */
.model-status-badge {
  font-size: 12px; padding: 3px 10px 3px 8px; border-radius: 8px; font-weight: 600;
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid;
}
.model-status-badge.idle { display: none; }
.model-status-badge.thinking { background: #f0f4ff; color: #4256b8; border-color: #6c80d4; }
.model-status-badge.calling_model { background: #fef0ff; color: #9448b3; border-color: #c97adb; }
.model-status-badge.tool_calling { background: #fff5e6; color: #a36600; border-color: #e0a13a; }
.model-status-badge.streaming { background: #e6f9f6; color: #158a80; border-color: #19c8b9; }
.model-status-badge.done { background: #e6f5e6; color: #2a7a2a; border-color: #4caf50; }
/* Animated dot for "in progress" states */
.model-status-dot {
  width: 6px; height: 6px; border-radius: 50%; background: currentColor; display: inline-block;
}
.model-status-badge.thinking .model-status-dot,
.model-status-badge.calling_model .model-status-dot,
.model-status-badge.tool_calling .model-status-dot,
.model-status-badge.streaming .model-status-dot {
  animation: status-blink 1.2s infinite ease-in-out;
}
@keyframes status-blink {
  0%, 100% { opacity: 0.3; transform: scale(0.85); }
  50%      { opacity: 1;   transform: scale(1.2); }
}

/* Connection indicator — always visible in header */
.connection-indicator { font-size: 12px; padding: 4px 12px; border-radius: 10px; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.connection-indicator.sse { background: #e6f9f6; color: #158a80; border: 1.5px solid #19c8b9; }
.connection-indicator.fallback { background: #fef6e6; color: #8a6d14; border: 1.5px solid #e8a735; }
.connection-indicator.connecting { background: #eef0f7; color: #4a5a8a; border: 1.5px solid #7889c4; }
.connection-indicator.unknown { background: #f5f3ed; color: #988B7A; border: 1.5px solid #d0c8b8; }

/* Message flow tag — shown on each assistant message */
.msg-flow-tag { font-size: 10px; padding: 2px 7px; border-radius: 6px; font-weight: 700; margin-left: 8px; vertical-align: middle; display: inline-block; }
.msg-flow-tag.sse { background: #e6f9f6; color: #158a80; border: 1px solid rgba(25,200,185,0.4); }
.msg-flow-tag.fallback { background: #fef6e6; color: #8a6d14; border: 1px solid rgba(232,167,53,0.4); }

/* Thinking block */
.thinking-block { margin: 4px 0; border-radius: 12px; border: 1px solid #d6c9a8; background: rgba(230,222,198,0.15); overflow: hidden; }
.thinking-block.thinking-done { border-color: #c9be9e; background: rgba(230,222,198,0.08); }
.thinking-header { display: flex; align-items: center; gap: 6px; padding: 8px 14px; cursor: pointer; font-size: 13px; color: #8a7b66; user-select: none; }
.thinking-icon { font-size: 14px; }
.thinking-label { font-weight: 700; }
.thinking-toggle { font-size: 11px; color: #b5a68e; margin-left: auto; }
.thinking-body { padding: 10px 14px; font-size: 13px; line-height: 1.6; color: #6d5f4b; border-top: 1px solid #d6c9a8; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
.thinking-block:not(.thinking-done) .thinking-header { color: #19c8b9; }
.thinking-block:not(.thinking-done) .thinking-icon { animation: pulse 1.2s infinite; }

/* Tool flow block */
.tool-flow-block { margin: 4px 0; display: flex; flex-direction: column; gap: 6px; }
.tool-step { border-radius: 10px; border: 1px solid #e8e2d6; background: rgba(255,255,255,0.7); padding: 8px 12px; }
.tool-step.calling { border-color: #19c8b9; background: rgba(230,249,246,0.4); }
.tool-step.running { border-color: #e8a735; background: rgba(254,246,230,0.4); }
.tool-step.success { border-color: #a3d977; background: rgba(242,251,230,0.4); }
.tool-step.error { border-color: #e85f5f; background: rgba(254,237,237,0.4); }
.tool-step-header { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.tool-step-icon { font-size: 14px; }
.tool-step-name { font-weight: 700; color: #4A3A28; }
.tool-step-state { font-size: 11px; color: #8a7b66; }
.tool-step-args { margin: 6px 0 0; font-size: 12px; color: #6d5f4b; }
.tool-step-args details summary { cursor: pointer; color: #8a7b66; font-size: 12px; }
.tool-step-args pre { margin: 4px 0; padding: 8px; background: #2d2d2d; border-radius: 8px; color: #e6db74; font-size: 12px; overflow-x: auto; white-space: pre-wrap; }
.tool-step-output { margin: 6px 0 0; font-size: 12px; color: #6d5f4b; line-height: 1.5; white-space: pre-wrap; }
.tool-step-output.streaming { color: #19c8b9; }
.tool-streaming-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #19c8b9; animation: pulse 1s infinite; margin-right: 4px; vertical-align: middle; }

/* Hint block */
.hint-block { margin: 4px 0; padding: 8px 12px; border-radius: 10px; background: rgba(230,249,246,0.3); border: 1px solid rgba(25,200,185,0.2); font-size: 13px; color: #4A3A28; }
.hint-icon { margin-right: 6px; }
.hint-text { white-space: pre-wrap; }

/* SOP card — rendered when AI emits a sop_card hint (after create_test_sop) */
.sop-card {
  margin: 8px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #EEEDFE 0%, #E1F5EE 100%);
  border: 1.5px solid #AFA9EC;
  box-shadow: 0 2px 8px rgba(83,74,183,0.08);
}
.sop-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.sop-icon { font-size: 20px; }
.sop-title { font-weight: 600; font-size: 14px; color: #3C3489; }
.sop-phase-badge {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
  background: #534AB7;
  color: white;
}
.sop-phase-badge.phase-1 { background: #378ADD; }
.sop-phase-badge.phase-2 { background: #1D9E75; }
.sop-phase-badge.phase-3 { background: #BA7517; }
.sop-phase-badge.phase-4 { background: #D85A30; }
.sop-requirement { font-size: 13px; color: #2C2C2A; margin: 6px 0; line-height: 1.5; }
.sop-cases { font-size: 13px; color: #2C2C2A; margin: 6px 0; }
.sop-cases ol { margin: 4px 0 0 20px; padding: 0; }
.sop-cases li { margin: 3px 0; }
.sop-hint {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.5);
  font-size: 13px;
  color: #3C3489;
  font-weight: 500;
}
.sop-hint .arrow { color: #1D9E75; font-weight: 600; margin-right: 4px; }

/* Task card — rendered when AI emits a task_card hint */
.task-card {
  margin: 8px 0;
  border: 1.5px solid #534AB7;
  border-radius: 12px;
  padding: 14px 16px;
  background: #FAF9F6;
  max-width: 420px;
  box-shadow: 0 2px 12px rgba(83,74,183,0.1);
  animation: card-appear 0.25s ease;
}
@keyframes card-appear { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.task-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.task-status-badge {
  font-size: 11px; padding: 2px 9px; border-radius: 10px; font-weight: 700; letter-spacing: 0.3px;
}
.task-status-badge.pending   { background: #EEF2FF; color: #4F46E5; border: 1px solid #C7D2FE; }
.task-status-badge.running   { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; animation: pulse-badge 1.5s infinite; }
.task-status-badge.completed { background: #D1FAE5; color: #065F46; border: 1px solid #6EE7B7; }
.task-status-badge.failed    { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
.task-status-badge.stopped   { background: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
.task-id { font-size: 11px; color: #9CA3AF; font-family: 'Cascadia Code', monospace; }
.task-title { font-size: 15px; font-weight: 700; color: #1F2937; margin-bottom: 6px; }
.task-meta { font-size: 12px; color: #6B7280; margin-bottom: 2px; }
.task-cases { margin: 6px 0 4px; border-top: 1px solid #F0EDE8; padding-top: 6px; }
.case-item { font-size: 12px; color: #374151; padding: 2px 0; display: flex; gap: 4px; }
.case-num { color: #9CA3AF; flex-shrink: 0; }
.case-more { font-size: 11px; color: #9CA3AF; padding: 2px 0; font-style: italic; }
.progress-bar { height: 4px; background: #E5E7EB; border-radius: 2px; margin: 8px 0 4px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 2px; transition: width 0.4s ease; background: linear-gradient(90deg, #818CF8, #534AB7); }
.progress-fill.completed { background: linear-gradient(90deg, #6EE7B7, #059669); }
.progress-fill.failed    { background: linear-gradient(90deg, #FCA5A5, #DC2626); }
.progress-label { font-size: 11px; color: #9CA3AF; text-align: right; margin-top: -2px; }
.task-actions { display: flex; gap: 8px; margin-top: 10px; }
.task-btn {
  flex: 1; padding: 6px 10px; border-radius: 8px; font-size: 12px; font-weight: 600;
  font-family: inherit; cursor: pointer; transition: all 0.15s; border: 1.5px solid;
}
.task-btn.primary   { background: #EEF2FF; color: #4F46E5; border-color: #C7D2FE; }
.task-btn.primary:hover { background: #E0E7FF; }
.task-btn.secondary { background: #F9FAFB; color: #374151; border-color: #D1D5DB; }
.task-btn.secondary:hover { background: #F3F4F6; }
.task-btn.danger    { background: #FEF2F2; color: #991B1B; border-color: #FCA5A5; }
.task-btn.danger:hover { background: #FEE2E2; }

/* Stop button */
.stop-btn { display: flex; align-items: center; gap: 4px; padding: 6px 14px; border: 1.5px solid #e85f5f; border-radius: 8px; background: none; color: #e85f5f; font-size: 13px; font-weight: 700; font-family: inherit; cursor: pointer; transition: all 0.15s; }
.stop-btn:hover { background: rgba(232,95,95,0.1); }

/* Model name tag in token display */
.model-name-tag { font-size: 10px; padding: 2px 7px; border-radius: 6px; background: rgba(25,200,185,0.1); color: #19c8b9; border: 1px solid rgba(25,200,185,0.3); margin-right: 6px; }

/* End reason badge — shown when reply ended abnormally */
.reason-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; padding: 4px 10px; border-radius: 8px; margin-top: 4px; font-weight: 600;
}
.reason-badge.exceed_max_iters { background: #fff3e0; color: #bf360c; border: 1px solid #ff8a65; }
.reason-badge.stopped { background: #f5f5f5; color: #616161; border: 1px solid #bdbdbd; }
.reason-badge.error { background: #ffebee; color: #b71c1c; border: 1px solid #ef5350; }

/* User confirmation dialog — P0 security: dangerous tool calls require explicit approval */
.confirm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 9999;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.confirm-dialog {
  background: #fff; border-radius: 16px; max-width: 560px; width: 100%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25); overflow: hidden; animation: dialog-appear 0.2s ease;
}
@keyframes dialog-appear { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.confirm-header {
  display: flex; align-items: center; gap: 10px; padding: 20px 24px;
  background: linear-gradient(135deg, #fff8e1, #fff3e0); border-bottom: 2px solid #ffcc02;
}
.confirm-icon { font-size: 24px; }
.confirm-title { font-size: 18px; font-weight: 700; color: #bf360c; }
.confirm-body { padding: 20px 24px; max-height: 400px; overflow-y: auto; }
.confirm-desc { font-size: 14px; color: #6d5f4b; margin: 0 0 14px; }
.confirm-tools { display: flex; flex-direction: column; gap: 10px; }
.confirm-tool-item {
  display: flex; align-items: flex-start; gap: 12px; padding: 14px;
  border-radius: 10px; border: 1.5px solid #e8e2d6; background: #faf9f4;
}
.confirm-tool-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.confirm-tool-info { flex: 1; min-width: 0; }
.confirm-tool-name { font-size: 14px; font-weight: 700; color: #4A3A28; display: block; margin-bottom: 6px; }
.confirm-tool-args {
  font-size: 12px; color: #6d5f4b; background: #fff; border-radius: 8px;
  padding: 8px 10px; margin: 0; overflow-x: auto; max-height: 120px;
  font-family: 'Cascadia Code', Consolas, monospace; white-space: pre;
}
.confirm-tool-actions { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.confirm-btn {
  padding: 7px 14px; border-radius: 8px; border: 1.5px solid; font-size: 13px;
  font-weight: 700; font-family: inherit; cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.confirm-btn.approve { background: #e8f5e9; color: #2e7d32; border-color: #66bb6a; }
.confirm-btn.approve:hover { background: #c8e6c9; }
.confirm-btn.deny { background: #ffebee; color: #c62828; border-color: #ef5350; }
.confirm-btn.deny:hover { background: #ffcdd2; }
.confirm-btn.cancel { background: #f5f5f5; color: #616161; border-color: #bdbdbd; }
.confirm-btn.cancel:hover { background: #eeeeee; }
.confirm-footer {
  display: flex; align-items: center; gap: 10px; padding: 16px 24px;
  background: #faf9f4; border-top: 1px solid #e8e2d6; flex-wrap: wrap;
}
.confirm-btn.approve-all { background: #e6f9f6; color: #158a80; border-color: #19c8b9; flex: 1; justify-content: center; }
.confirm-btn.approve-all:hover { background: #b2dfdb; }
.confirm-btn.deny-all { background: #ffebee; color: #c62828; border-color: #ef5350; flex: 1; justify-content: center; }
.confirm-btn.deny-all:hover { background: #ffcdd2; }

.chat-body { flex: 1; overflow-y: auto; padding: 24px 28px; display: flex; flex-direction: column; gap: 22px; background: #faf9f4; }
.msg { display: flex; gap: 14px; max-width: 80%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.msg.assistant { align-self: flex-start; }
.msg-avatar { width: 44px; height: 44px; border-radius: 12px; background: #fff; border: 1px solid #e8e2d6; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; overflow: hidden; box-shadow: 0 2px 8px rgba(61,52,40,0.08); }
.msg-content { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.msg-author { font-size: 13px; font-weight: 700; color: #a0936e; padding: 0 6px; }
.msg.user .msg-author { text-align: right; }
.msg-text { padding: 16px 20px; border-radius: 18px; font-size: 15px; line-height: 1.75; white-space: pre-wrap; word-break: break-word; box-shadow: 0 2px 10px rgba(61,52,40,0.08); }
.msg.user .msg-text { background: linear-gradient(135deg, #19c8b9 0%, #15a89c 100%); color: #fff; border-bottom-right-radius: 6px; }
.msg.assistant .msg-text { background: #fff; color: #4A3A28; border: 1px solid #e8e2d6; border-bottom-left-radius: 6px; }
.msg-tokens { font-size: 11px; color: #a0936e; padding: 0 6px; }

/* Markdown */
.msg-text :deep(p) { margin: 0 0 8px; }
.msg-text :deep(p:last-child) { margin-bottom: 0; }
.msg-text :deep(code) { font-family: 'Cascadia Code', Consolas, monospace; font-size: 13px; padding: 2px 6px; border-radius: 6px; background: rgba(0,0,0,0.06); }
.msg.user .msg-text :deep(code) { background: rgba(255,255,255,0.2); }
.msg-text :deep(pre) { margin: 10px 0; padding: 14px 16px; border-radius: 12px; background: #2d2d2d; overflow-x: auto; }
.msg-text :deep(pre code) { background: transparent; padding: 0; font-size: 13px; line-height: 1.6; color: #e6db74; }
.msg-text :deep(ul), .msg-text :deep(ol) { margin: 6px 0; padding-left: 22px; }
.msg-text :deep(li) { margin-bottom: 3px; line-height: 1.6; }
.msg-text :deep(table) { width: 100%; margin: 10px 0; border-collapse: collapse; font-size: 13px; }
.msg-text :deep(th) { background: rgba(0,0,0,0.05); font-weight: 700; padding: 8px 12px; border: 1px solid rgba(0,0,0,0.1); text-align: left; }
.msg-text :deep(td) { padding: 6px 12px; border: 1px solid rgba(0,0,0,0.08); }
.msg-text :deep(blockquote) { margin: 8px 0; padding: 8px 14px; border-left: 3px solid rgba(25,200,185,0.5); background: rgba(25,200,185,0.06); border-radius: 0 8px 8px 0; }
.msg-text :deep(h1), .msg-text :deep(h2) { margin: 12px 0 6px; font-weight: 700; }
.msg-text :deep(a) { color: #19c8b9; text-decoration: underline; }

.mermaid-placeholder { opacity: 0.6; transition: opacity 0.2s; }
.mermaid-diagram { margin: 10px 0; padding: 14px; background: #fff; border-radius: 12px; border: 2px solid #19c8b9; overflow-x: auto; display: flex; justify-content: center; }
.mermaid-diagram svg { max-width: 100%; height: auto; }

/* Typing */
.typing { display: flex; align-items: center; gap: 6px; min-height: 28px; }
.typing span { width: 9px; height: 9px; border-radius: 50%; background: #19c8b9; animation: bounce 1.4s ease-in-out infinite; }
.typing span:nth-child(1) { animation-delay: 0s; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-7px); } }

/* File preview */
.file-preview { display: flex; align-items: center; gap: 8px; padding: 8px 14px; margin: 0 24px; background: #e6f9f6; border: 1px solid #19c8b9; border-radius: 10px; font-size: 13px; }
.file-preview-icon { font-size: 16px; }
.file-preview-name { font-weight: 600; color: #158a80; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-preview-size { color: #6b5b48; white-space: nowrap; }
.file-preview-remove { margin-left: auto; border: none; background: none; cursor: pointer; font-size: 16px; color: #e85f5f; padding: 2px 6px; border-radius: 4px; }
.file-preview-remove:hover { background: rgba(232,95,95,0.1); }

/* Input */
.upload-btn { display: flex; align-items: center; justify-content: center; width: 42px; height: 42px; border: 2px solid #e8e2d6; border-radius: 12px; background: #faf9f4; font-size: 20px; cursor: pointer; transition: all 0.2s ease; flex-shrink: 0; }
.upload-btn:hover { border-color: #19c8b9; background: #e6f9f6; }
.upload-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chat-input { display: flex; align-items: flex-end; gap: 14px; padding: 18px 24px; border-top: 2px solid #e8e2d6; background: #fff; flex-shrink: 0; }
.input-box { flex: 1; }
.chat-input :deep(.el-textarea__inner) { background: #faf9f4; border: 1.5px solid #e8e2d6; border-radius: 14px; padding: 14px 18px; font-size: 15px; line-height: 1.7; color: #4A3A28; resize: none; transition: all 0.2s ease; font-family: inherit; }
.chat-input :deep(.el-textarea__inner:focus) { background: #fff; border-color: #19c8b9; box-shadow: 0 0 0 4px rgba(25,200,185,0.12); }
.send-btn { display: flex; align-items: center; gap: 8px; padding: 14px 26px; border: none; border-radius: 14px; background: linear-gradient(135deg, #19c8b9 0%, #15a89c 100%); color: #fff; font-size: 16px; font-weight: 700; font-family: inherit; cursor: pointer; transition: all 0.2s ease; flex-shrink: 0; box-shadow: 0 4px 14px rgba(25,200,185,0.35); }
.send-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(25,200,185,0.5); }
.send-btn:disabled { background: #d0c8b8; box-shadow: none; cursor: not-allowed; opacity: 0.6; }
</style>
