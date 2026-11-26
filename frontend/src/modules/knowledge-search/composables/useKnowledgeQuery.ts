import { ref } from "vue"
import { formatApiError } from "@/shared/api-client"
import { queryKnowledge } from "../api"
import { KS_TRANSPORT_ERROR } from "../constants"
import type { QueryResult } from "../types"

export function useKnowledgeQuery() {
  const question = ref("")
  const loading = ref(false)
  const outcome = ref<QueryResult | null>(null)

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
