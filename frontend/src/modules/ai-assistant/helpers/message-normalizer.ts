/** message-normalizer — 消息数据标准化（从 useMessageStore 提取） */
import type { ChatMessage, ContentBlock, SSERound, ToolCall, ToolState } from '@/shared/types/ai'

/** 从 hint block 解析 hint 内容（处理 string / JSON object） */
export function parseHintFromBlocks(hintBlock: ContentBlock | null): object | string | null {
  if (!hintBlock) return null
  const raw = hintBlock.hint as string | object
  if (typeof raw === 'object') return raw
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return raw }
  }
  return null
}

/** tool_call 块参数展示文本：inputRaw 优先，其次 input（原生块是 JSON 字符串） */
function toolInputToDisplay(c: ContentBlock | {}): string {
  const raw = (c as { inputRaw?: string }).inputRaw
  if (raw) return raw
  const input = (c as { input?: unknown }).input
  if (input == null) return ''
  return typeof input === 'string' ? input : JSON.stringify(input)
}

/** 从 tool_result 块提取纯文本输出（persisted 的 output 为块列表时取 text 块拼接） */
function toolResultText(result: ContentBlock | undefined): string {
  if (!result) return ''
  const output = (result as { output?: unknown }).output
  if (typeof output === 'string') return output
  if (Array.isArray(output)) {
    return output
      .filter((b) => (b as { type?: string })?.type === 'text')
      .map((b) => (b as { text?: string })?.text || '')
      .join('\n')
  }
  return ''
}

/** 从 tool_result 块提取图片 data URI（兼容 live 的 data/mediaType 与 persisted 的 output 列表两种形态） */
export function toolResultImage(result: ContentBlock | undefined): string {
  if (!result) return ''
  const r = result as { data?: unknown; mediaType?: string; output?: unknown }
  // live 形态：SSEMessageBuilder 累积的兄弟字段 data/mediaType（base64）
  if (typeof r.data === 'string' && r.data) {
    return `data:${r.mediaType || 'image/png'};base64,${r.data}`
  }
  // persisted 形态：output 为块列表，含 data 块
  if (Array.isArray(r.output)) {
    const dataBlock = r.output.find((b) => (b as { type?: string })?.type === 'data')
    const src = (dataBlock as { source?: { data?: string; media_type?: string } })?.source
    if (src?.data) return `data:${src.media_type || 'image/png'};base64,${src.data}`
  }
  return ''
}

/** 由 tool_call + tool_result 块组装一个 ToolCall UI 对象 */
function buildToolCall(call: ContentBlock | {}, result?: ContentBlock): ToolCall {
  const c = call as ContentBlock
  const img = toolResultImage(result)
  return {
    id: (c.id as string) || '',
    name: (c.name as string) || '',
    displayArgs: toolInputToDisplay(call),
    state: (result?.state as ToolState) || 'success',
    output: toolResultText(result),
    ...(img ? { resultImage: img } : {}),
  }
}

/** 从 persisted blocks 重建 toolFlow 数组 */
export function rebuildToolFlow(blocks: ContentBlock[]): ToolCall[] {
  if (!blocks.length) return []
  const pairs = blocks.filter(b => b.type === 'tool_pair')
  if (pairs.length) {
    return pairs.map(p => buildToolCall((p.call as ContentBlock) || {}, (p.result as ContentBlock)))
  }
  const calls = blocks.filter(b => b.type === 'tool_call')
  const results = blocks.filter(b => b.type === 'tool_result')
  return calls.map(c => buildToolCall(c, results.find(res => res.id === c.id)))
}

/** 从 persisted content blocks 重建 per-round ReAct 分组 */
export function rebuildRoundsFromBlocks(blocks: ContentBlock[]): SSERound[] {
  if (!blocks || !blocks.length) return []

  const toolPairs = blocks.filter(b => b.type === 'tool_pair')
  const hasPairs = toolPairs.length > 0

  const thinkingByRound: Record<number, string> = {}
  for (const b of blocks) {
    if (b.type === 'thinking' && typeof (b as unknown as { roundIndex?: number }).roundIndex === 'number') {
      thinkingByRound[(b as unknown as { roundIndex: number }).roundIndex] = (b as unknown as { thinking: string }).thinking || ''
    }
  }

  const toolsByRound: Record<number, ToolCall[]> = {}
  if (hasPairs) {
    for (const p of toolPairs) {
      const ri = (p.call as ContentBlock & { roundIndex?: number })?.roundIndex
      if (typeof ri !== 'number') continue
      if (!toolsByRound[ri]) toolsByRound[ri] = []
      toolsByRound[ri].push(buildToolCall((p.call as ContentBlock) || {}, (p.result as ContentBlock)))
    }
  } else {
    const toolCalls = blocks.filter(b => b.type === 'tool_call')
    const toolResults = blocks.filter(b => b.type === 'tool_result')
    for (const c of toolCalls) {
      const ri = (c as ContentBlock & { roundIndex?: number }).roundIndex
      if (typeof ri !== 'number') continue
      const r = toolResults.find(res => res.id === c.id)
      if (!toolsByRound[ri]) toolsByRound[ri] = []
      toolsByRound[ri].push(buildToolCall(c, r))
    }
  }

  const allIndices = new Set([
    ...Object.keys(thinkingByRound).map(Number),
    ...Object.keys(toolsByRound).map(Number),
  ])
  if (allIndices.size === 0) return []

  return [...allIndices].sort((a, b) => a - b).map(ri => ({
    thinking: thinkingByRound[ri] || '',
    thinkingDone: true,
    thinkingExpanded: false,
    tools: toolsByRound[ri] || [],
  }))
}

/** 标准化从后端加载的消息数据 */
export function normalizeLoadedMessage(m: Record<string, unknown>): ChatMessage | null {
  if (!m || typeof m !== 'object') return null
  const flow = m.role === 'assistant' ? ((m.flow as string) === 'sse' ? (m.flow as string) : null) : null
  const blocks = Array.isArray(m.blocks) ? m.blocks as ContentBlock[] : []
  const rounds = m.role === 'assistant' ? rebuildRoundsFromBlocks(blocks) : []
  const textBlock = blocks.find(b => b?.type === 'text')
  const thinkingBlock = !rounds.length ? blocks.find(b => b?.type === 'thinking') : null
  const toolBlocks = !rounds.length ? blocks.filter(b => b?.type === 'tool_call' || b?.type === 'tool_result' || b?.type === 'tool_pair') : []
  const hintBlock = blocks.find(b => b?.type === 'hint')
  const content = typeof m.content === 'string' ? m.content : (textBlock as { text?: string })?.text || ''

  return {
    ...m as unknown as ChatMessage,
    flow,
    content,
    blocks,
    rounds,
    thinking: (thinkingBlock as { thinking?: string })?.thinking || '',
    thinkingDone: !!(thinkingBlock as { thinking?: string })?.thinking,
    toolFlow: rounds.length ? [] : rebuildToolFlow(toolBlocks),
    hint: parseHintFromBlocks(hintBlock || null),
    reason: (m.reason as ChatMessage['reason']) || 'normal',
  }
}
