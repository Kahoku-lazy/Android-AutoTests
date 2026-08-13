/** useMessageStore — 消息状态管理（TypeScript） */
import { ref, type Ref } from 'vue'
import type { ChatMessage, ContentBlock } from '@/shared/types/ai'
import { normalizeLoadedMessage } from '../helpers/message-normalizer'

export interface UseMessageStoreReturn {
  messages: Ref<ChatMessage[]>
  assistIdx: Ref<number>
  backgroundStreamConvId: Ref<number | null>
  hydrateMessages: (dataMessages: unknown[]) => void
  appendUserAndAssistantPlaceholder: (displayText: string, blocks?: ContentBlock[]) => number
  clearMessages: () => void
  normalizeLoadedMessage: typeof normalizeLoadedMessage
}

let _msgSeq = 0

export function useMessageStore(): UseMessageStoreReturn {
  const messages = ref<ChatMessage[]>([])
  const assistIdx = ref(-1)
  const backgroundStreamConvId = ref<number | null>(null)

  function hydrateMessages(dataMessages: unknown[]) {
    messages.value = dataMessages
      .map(m => normalizeLoadedMessage(m as Record<string, unknown>))
      .filter((m): m is ChatMessage => m !== null)
    assistIdx.value = -1  // reset — will be set by appendUserAndAssistantPlaceholder on next send
  }

  function appendUserAndAssistantPlaceholder(displayText: string, blocks?: ContentBlock[]): number {
    const uid = `u${++_msgSeq}`
    messages.value.push({
      id: uid,
      role: 'user',
      content: displayText,
      ...(blocks?.length ? { blocks } : {}),
    })
    const aid = `a${++_msgSeq}`
    assistIdx.value = messages.value.length
    messages.value.push({
      id: aid,
      role: 'assistant',
      content: '',
      tokens: 0,
      flow: null,
      rounds: [],
      deliveryStatus: 'sending',
    })
    return assistIdx.value
  }

  function clearMessages() {
    messages.value = []
    assistIdx.value = -1
  }

  return {
    messages, assistIdx, backgroundStreamConvId,
    hydrateMessages, appendUserAndAssistantPlaceholder, clearMessages,
    normalizeLoadedMessage,
  }
}
