/** useLogKeywords — 串口日志页「日志关键词」Tab：只读目录取数 + 表格行 + 搜索 / 范围筛选（无写操作） */
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
  /** 范围筛选：默认全部；选项恒从全量行派生（搜索 / 筛选不改变选项） */
  const scope = ref(SCOPE_FILTER_ALL)
  let loaded = false

  const rows = computed(() => buildKeywordRows(catalog.value?.keywords || []))
  const filteredRows = computed(() =>
    filterKeywordRows(filterKeywordRowsByScope(rows.value, scope.value), query.value),
  )
  const scopeFilterOptions = computed(() => scopeOptions(rows.value))
  /** 计数永远报**全量**（搜索 / 范围筛选时也一样），避免让人以为表变小了 */
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

  /** 首次进入该来源时按需加载（后续切换回来不再重复请求） */
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
