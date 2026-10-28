/** BUG 单列表状态：服务端过滤、统计、分页与历史同步。 */
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { ElMessage } from "element-plus"
import { usePagination } from "@/shared/composables/usePagination"
import { listBugs, syncBugs } from "../api"
import { BUG_CATEGORY_TABS, BUG_PAGE_SIZE_OPTIONS, BUG_SYNC } from "../constants"
import type { BugStatus, BugSummary, BugTicket } from "../types"

const EMPTY_SUMMARY: BugSummary = {
  total: 0,
  ui_automation: 0,
  case_authoring: 0,
  open: 0,
  resolved: 0,
  ignored: 0,
}

const KEYWORD_DEBOUNCE_MS = 350

export function useBugList() {
  const tickets = ref<BugTicket[]>([])
  const total = ref(0)
  const summary = ref<BugSummary>({ ...EMPTY_SUMMARY })
  const loading = ref(false)
  const syncing = ref(false)
  const error = ref("")
  const category = ref<string>("all")
  const status = ref<BugStatus | "">("")
  const keyword = ref("")

  let keywordTimer: ReturnType<typeof setTimeout> | null = null

  async function load() {
    loading.value = true
    error.value = ""
    try {
      const params: { category?: string; status?: string; keyword?: string } = {}
      if (category.value !== "all") params.category = category.value
      if (status.value) params.status = status.value
      const text = keyword.value.trim()
      if (text) params.keyword = text
      const { data } = await listBugs(params)
      if (!data.status || !data.data) throw new Error(data.message || "加载 BUG 单失败")
      tickets.value = data.data.items
      summary.value = data.data.summary
      total.value = data.data.total
    } catch (e) {
      error.value = errorMessage(e, "加载 BUG 单失败")
    } finally {
      loading.value = false
    }
  }

  async function sync() {
    syncing.value = true
    try {
      const { data } = await syncBugs()
      if (!data.status || !data.data) throw new Error(data.message || "同步历史错误失败")
      const result = data.data
      const message = result.created
        ? `${BUG_SYNC.done}：新增 ${result.created} 张，更新 ${result.updated} 张`
        : BUG_SYNC.empty
      ElMessage.success(message)
      await load()
    } catch (e) {
      ElMessage.error(errorMessage(e, "同步历史错误失败"))
    } finally {
      syncing.value = false
    }
  }

  const categoryTabs = computed(() =>
    BUG_CATEGORY_TABS.map((tab) => ({
      ...tab,
      count:
        tab.key === "all"
          ? summary.value.total
          : tab.key === "ui_automation"
            ? summary.value.ui_automation
            : summary.value.case_authoring,
    })),
  )

  const { PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems, setPageSize, goPage } =
    usePagination(tickets, { options: BUG_PAGE_SIZE_OPTIONS })

  watch([category, status], () => {
    currentPage.value = 1
    load()
  })

  watch(keyword, () => {
    currentPage.value = 1
    if (keywordTimer) clearTimeout(keywordTimer)
    keywordTimer = setTimeout(load, KEYWORD_DEBOUNCE_MS)
  })

  onMounted(load)
  onUnmounted(() => {
    if (keywordTimer) clearTimeout(keywordTimer)
  })

  return {
    tickets,
    total,
    summary,
    loading,
    syncing,
    error,
    category,
    status,
    keyword,
    categoryTabs,
    PAGE_SIZE_OPTIONS,
    pageSize,
    currentPage,
    totalPages,
    pagedItems,
    setPageSize,
    goPage,
    load,
    sync,
  }
}

function errorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === "object") {
    const response = (error as { response?: { data?: { message?: string } } }).response
    if (response?.data?.message) return response.data.message
    const message = (error as { message?: string }).message
    if (message) return message
  }
  return fallback
}
