import { ref } from 'vue'
import type { ToolCall } from '@/shared/types/ai'

export interface UseToolCallsReturn {
  toolCalls: ReturnType<typeof ref<ToolCall[]>>
  resetToolCalls: () => void
}

export function useToolCalls(): UseToolCallsReturn {
  const toolCalls = ref<ToolCall[]>([])

  function resetToolCalls() {
    toolCalls.value = []
  }

  return { toolCalls, resetToolCalls }
}
