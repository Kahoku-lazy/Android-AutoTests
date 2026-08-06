/** message-normalizer — 消息数据标准化（从 useMessageStore 提取） */
import type { ChatMessage, ContentBlock, SSERound, ToolCall } from '@/shared/types/ai'

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

/** 从 persisted blocks 重建 toolFlow 数组 */
export function rebuildToolFlow(blocks: ContentBlock[]): ToolCall[] {
  if (!blocks.length) return []
  const pairs = blocks.filter(b => b.type === 'tool_pair')
  if (pairs.length) {
    return pairs.map(p => ({
      id: (p.call as ContentBlock)?.id as string || '',
      name: (p.call as ContentBlock)?.name as string || '',
      displayArgs: ((p.call as { inputRaw?: string; input?: object }).inputRaw as string)
        || (((p.call as { input?: object }).input) ? JSON.stringify((p.call as { input?: object }).input) : ''),
      state: ((p.result as ContentBlock)?.state as string) || 'success',
      output: ((p.result as ContentBlock)?.output as string) || '',
    }))
  }
  const calls = blocks.filter(b => b.type === 'tool_call')
  const results = blocks.filter(b => b.type === 'tool_result')
  return calls.map(c => {
    const r = results.find(res => res.id === c.id)
    return {
      id: (c.id as string) || '',
      name: (c.name as string) || '',
      displayArgs: ((c as { inputRaw?: string; input?: object }).inputRaw as string)
        || ((c as { input?: object }).input ? JSON.stringify((c as { input?: object }).input) : ''),
      state: (r?.state as string) || 'success',
      output: (r?.output as string) || '',
    }
  })
}

/** 从 persisted content blocks 重建 per-round ReAct 分组 */
export function rebuildRoundsFromBlocks(blocks: ContentBlock[]): SSERound[] {
  if (!blocks || !blocks.length) return []

  const toolPairs = blocks.filter(b => b.type === 'tool_pair')
  const hasPairs = toolPairs.length > 0

  const thinkingByRound: Record<number, string> = {}
  for (const b of blocks) {
    if (b.type === 'thinking' && typeof (b as { roundIndex?: number }).roundIndex === 'number') {
      thinkingByRound[(b as { roundIndex: number }).roundIndex] = (b as { thinking: string }).thinking || ''
    }
  }

  const toolsByRound: Record<number, ToolCall[]> = {}
  if (hasPairs) {
    for (const p of toolPairs) {
      const ri = (p.call as ContentBlock & { roundIndex?: number })?.roundIndex
      if (typeof ri !== 'number') continue
      if (!toolsByRound[ri]) toolsByRound[ri] = []
      toolsByRound[ri].push({
        id: (p.call as ContentBlock)?.id as string || '',
        name: (p.call as ContentBlock)?.name as string || '',
        displayArgs: ((p.call as { inputRaw?: string; input?: object }).inputRaw as string) || '',
        state: ((p.result as ContentBlock)?.state as string) || 'success',
        output: ((p.result as ContentBlock)?.output as string) || '',
      })
    }
  } else {
    const toolCalls = blocks.filter(b => b.type === 'tool_call')
    const toolResults = blocks.filter(b => b.type === 'tool_result')
    for (const c of toolCalls) {
      const ri = (c as ContentBlock & { roundIndex?: number }).roundIndex
      if (typeof ri !== 'number') continue
      const r = toolResults.find(res => res.id === c.id)
      if (!toolsByRound[ri]) toolsByRound[ri] = []
      toolsByRound[ri].push({
        id: (c.id as string) || '',
        name: (c.name as string) || '',
        displayArgs: ((c as { inputRaw?: string }).inputRaw as string) || '',
        state: (r?.state as string) || 'success',
        output: (r?.output as string) || '',
      })
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
    rounds,
    thinking: (thinkingBlock as { thinking?: string })?.thinking || '',
    thinkingDone: !!(thinkingBlock as { thinking?: string })?.thinking,
    toolFlow: rounds.length ? [] : rebuildToolFlow(toolBlocks),
    hint: parseHintFromBlocks(hintBlock || null),
    reason: (m.reason as ChatMessage['reason']) || 'normal',
  }
}
