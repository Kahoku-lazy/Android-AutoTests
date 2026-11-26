import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { usePagination } from "@/shared/composables/usePagination"
import { listReports, type ReportListParams } from "../api"
import { FILTER_DEBOUNCE, PAGE_SIZE_OPTIONS, REPORT_MESSAGES, SOURCE_TABS } from "../constants"
import type { ReportRow, ReportSummary } from "../types"

const EMPTY_SUMMARY: ReportSummary = { total_reports: 0, sop_reports: 0, agent_reports: 0 }

export function useReportInventory() {
  const items = ref<ReportRow[]>([])
  const total = ref(0)
  const summary = ref<ReportSummary>({ ...EMPTY_SUMMARY })
  const loading = ref(false)
  const error = ref("")
  const source = ref<string>("all")
  const keyword = ref("")
  const dateRange = ref<[string, string] | null>(null)

  let keywordTimer: ReturnType<typeof setTimeout> | null = null

  async function load() {
    loading.value = true
    error.value = ""
    try {
      const params: ReportListParams = {}
      if (source.value !== "all") params.source = source.value
      const text = keyword.value.trim()
      if (text) params.keyword = text
      if (dateRange.value) {
        params.start_date = dateRange.value[0]
        params.end_date = dateRange.value[1]
      }
      const { data } = await listReports(params)
      if (!data.status || !data.data) throw new Error(data.message || REPORT_MESSAGES.loadFailed)
      items.value = data.data.items
      summary.value = data.data.summary
      total.value = data.data.total
    } catch (e) {
      error.value = errorMessage(e, REPORT_MESSAGES.loadFailed)
    } finally {
      loading.value = false
    }
  }

  const sourceTabs = computed(() =>
    SOURCE_TABS.map((tab) => ({
      ...tab,
      count:
        tab.key === "all"
          ? summary.value.total_reports
          : tab.key === "sop"
            ? summary.value.sop_reports
            : summary.value.agent_reports,
    })),
  )

  const { pageSize, currentPage, totalPages, pagedItems, setPageSize, goPage } = usePagination(
    items,
    { options: PAGE_SIZE_OPTIONS },
  )

  watch([source, dateRange], () => {
    currentPage.value = 1
    load()
  })

  watch(keyword, () => {
    currentPage.value = 1
    if (keywordTimer) clearTimeout(keywordTimer)
    keywordTimer = setTimeout(load, FILTER_DEBOUNCE)
  })

  onMounted(load)
  onUnmounted(() => {
    if (keywordTimer) clearTimeout(keywordTimer)
  })

  return {
    items,
    total,
    summary,
    loading,
    error,
    source,
    keyword,
    dateRange,
    sourceTabs,
    PAGE_SIZE_OPTIONS,
    pageSize,
    currentPage,
    totalPages,
    pagedItems,
    setPageSize,
    goPage,
    load,
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
