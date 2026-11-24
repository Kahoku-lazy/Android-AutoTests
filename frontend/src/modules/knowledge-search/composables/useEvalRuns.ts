import { onScopeDispose, ref } from "vue"
import { formatApiError } from "@/shared/api-client"
import { fetchEvalRun, fetchEvalRuns, triggerEval } from "../api"
import { KS_EVAL_POLL_MS } from "../constants"
import type { EvalRun, EvalRunDetail, EvalTriggerPayload } from "../types"

export function useEvalRuns() {
  const runs = ref<EvalRun[]>([])
  const loading = ref(false)
  const error = ref("")
  const detail = ref<EvalRunDetail | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null

  function stopPolling(): void {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  async function load(): Promise<void> {
    loading.value = true
    error.value = ""
    try {
      const response = await fetchEvalRuns()
      if (response.status) {
        runs.value = response.data?.runs ?? []
      } else {
        error.value = response.message || "评测列表加载失败"
      }
    } catch (exc) {
      error.value = formatApiError(exc)
    } finally {
      loading.value = false
    }
  }

  async function selectRun(id: number): Promise<void> {
    stopPolling()
    try {
      const response = await fetchEvalRun(id)
      if (response.status && response.data) {
        detail.value = response.data
        if (response.data.status === "pending" || response.data.status === "running") {
          startPolling(id)
        }
      } else {
        error.value = response.message || "评测详情加载失败"
      }
    } catch (exc) {
      error.value = formatApiError(exc)
    }
  }

  function startPolling(id: number): void {
    stopPolling()
    timer = setInterval(async () => {
      try {
        const response = await fetchEvalRun(id)
        if (!response.status || !response.data) return
        detail.value = response.data
        if (response.data.status === "done" || response.data.status === "failed") {
          stopPolling()
          await load()
        }
      } catch {}
    }, KS_EVAL_POLL_MS)
  }

  async function trigger(payload: EvalTriggerPayload): Promise<{ ok: boolean; message: string }> {
    try {
      const response = await triggerEval(payload)
      if (!response.status || !response.data) {
        return { ok: false, message: response.message || "触发评测失败" }
      }
      await load()
      await selectRun(response.data.id)
      return { ok: true, message: "" }
    } catch (exc) {
      return { ok: false, message: formatApiError(exc) }
    }
  }

  onScopeDispose(stopPolling)

  return { runs, loading, error, detail, load, selectRun, trigger, stopPolling }
}
