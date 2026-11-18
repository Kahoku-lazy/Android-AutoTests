/** useKnowledgeQuery — 提问与三态结果：加载期不渲染空态，no_hit 与 unavailable 文案分开。 */
import { ref } from "vue"
import { formatApiError } from "@/shared/api-client"
import { queryKnowledge } from "../api"
import { KS_TRANSPORT_ERROR } from "../constants"
import type { QueryResult } from "../types"

export function useKnowledgeQuery() {
  const question = ref("")
  const loading = ref(false)
  const outcome = ref<QueryResult | null>(null)
  /** 传输层/信封错误（与业务三态分开）。 */
  const transportError = ref("")

  async function ask(bases: string[]): Promise<void> {
    const text = question.value.trim()
    if (!text || bases.length === 0 || loading.value) return
    loading.value = true
    transportError.value = ""
    outcome.value = null
    try {
      const response = await queryKnowledge({ question: text, bases })
      if (response.status && response.data) {
        outcome.value = response.data
      } else {
        transportError.value = response.message || KS_TRANSPORT_ERROR
      }
    } catch (exc) {
      transportError.value = formatApiError(exc) || KS_TRANSPORT_ERROR
    } finally {
      loading.value = false
    }
  }

  return { question, loading, outcome, transportError, ask }
}
