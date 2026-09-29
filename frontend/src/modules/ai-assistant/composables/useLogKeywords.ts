/** useLogKeywords — 工具箱「日志关键词」来源：只读目录取数 + 表格行 + 搜索（无写操作） */
import { computed, ref } from "vue"
import { fetchLogKeywords, type LogKeywordCatalog } from "../api/toolbox"
import { buildKeywordRows, filterKeywordRows, keywordRowCounts } from "../helpers/log-keyword-rows"
import { formatApiError } from "@/shared/api-client"

export function useLogKeywords() {
  const catalog = ref<LogKeywordCatalog | null>(null)
  const loading = ref(false)
  const loadError = ref("")
  const query = ref("")
  let loaded = false

  const rows = computed(() => buildKeywordRows(catalog.value?.keywords || []))
  const filteredRows = computed(() => filterKeywordRows(rows.value, query.value))
  /** 计数永远报**全量**（搜索时也一样），避免让人以为表变小了 */
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
    rows,
    filteredRows,
    counts,
    emptyNote,
    load,
    ensureLoaded,
  }
}
