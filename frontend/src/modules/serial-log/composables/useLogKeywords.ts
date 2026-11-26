import { computed, ref } from "vue"
import { fetchLogKeywords, type LogKeywordCatalog } from "../api"
import {
  SCOPE_FILTER_ALL,
  buildKeywordRows,
  filterKeywordRows,
  filterKeywordRowsByScope,
  keywordRowCounts,
  scopeOptions,
} from "../helpers/log-keyword-rows"
import { formatApiError } from "@/shared/api-client"

export function useLogKeywords() {
  const catalog = ref<LogKeywordCatalog | null>(null)
  const loading = ref(false)
  const loadError = ref("")
  const query = ref("")

  const scope = ref(SCOPE_FILTER_ALL)
  let loaded = false

  const rows = computed(() => buildKeywordRows(catalog.value?.keywords || []))
  const filteredRows = computed(() =>
    filterKeywordRows(filterKeywordRowsByScope(rows.value, scope.value), query.value),
  )
  const scopeFilterOptions = computed(() => scopeOptions(rows.value))

  const counts = computed(() => keywordRowCounts(rows.value))
  const emptyNote = computed(() => catalog.value?.note || "")

  async function load(): Promise<void> {
    loading.value = true
    loadError.value = ""
    try {
      const data = await fetchLogKeywords()
      if (data.status && data.data) {
        catalog.value = data.data
        loaded = true
      } else {
        loadError.value = data.message || "日志关键词加载失败"
      }
    } catch (e) {
      loadError.value = formatApiError(e, "日志关键词加载失败")
    }
    loading.value = false
  }

  async function ensureLoaded(): Promise<void> {
    if (loaded || loading.value) return
    await load()
  }

  return {
    catalog,
    loading,
    loadError,
    query,
    scope,
    rows,
    filteredRows,
    scopeFilterOptions,
    counts,
    emptyNote,
    load,
    ensureLoaded,
  }
}
