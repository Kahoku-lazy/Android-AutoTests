/** useMessageStore — 消息状态管理（TypeScript） */
import { ref, type Ref } from 'vue'
import type { ChatMessage } from '@/shared/types/ai'
import { normalizeLoadedMessage } from '../helpers/message-normalizer'

export interface UseMessageStoreReturn {
  messages: Ref<ChatMessage[]>
  assistIdx: Ref<number>
  backgroundStreamConvId: Ref<number | null>
  hydrateMessages: (dataMessages: unknown[]) => void
  appendUserAndAssistantPlaceholder: (displayText: string) => number
  clearMessages: () => void
  normalizeLoadedMessage: typeof normalizeLoadedMessage
}

export function useMessageStore(): UseMessageStoreReturn {
  const messages = ref<ChatMessage[]>([])
  const assistIdx = ref(-1)
  const backgroundStreamConvId = ref<number | null>(null)

  function hydrateMessages(dataMessages: unknown[]) {
    messages.value = dataMessages
      .map(m => normalizeLoadedMessage(m as Record<string, unknown>))
      .filter((m): m is ChatMessage => m !== null)
  }

  function appendUserAndAssistantPlaceholder(displayText: string): number {
    messages.value.push({ role: 'user', content: displayText })
    assistIdx.value = messages.value.length
    messages.value.push({
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
