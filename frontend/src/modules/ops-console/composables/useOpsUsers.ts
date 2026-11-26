import { computed, ref, watch } from "vue"
import { formatApiError } from "@/shared/api-client"
import { listOpsUsers } from "../api"
import { OPS_DEFAULT_PAGE_SIZE, OPS_KEYWORD_DEBOUNCE_MS } from "../constants"
import type { OpsStatusFilter, OpsUser } from "../types"

const LOAD_FAILED = "账号列表加载失败"

export function useOpsUsers() {
  const users = ref<OpsUser[]>([])
  const total = ref(0)
  const page = ref(1)

  const pageSize = OPS_DEFAULT_PAGE_SIZE
  const keyword = ref("")
  const status = ref<OpsStatusFilter>("all")
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref("")
  const selectedIds = ref<number[]>([])

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
  const showEmpty = computed(() => loaded.value && !loading.value && users.value.length === 0)

  async function load(): Promise<void> {
    loading.value = true
    error.value = ""
    try {
      const { data } = await listOpsUsers({
        page: page.value,
        page_size: pageSize,
        keyword: keyword.value.trim() || undefined,
        active: status.value === "all" ? undefined : status.value === "active" ? "true" : "false",
      })
      if (!data.status || !data.data) throw data
      users.value = data.data.users
      total.value = data.data.total
      loaded.value = true
    } catch (e) {
      error.value = formatApiError(e as never, LOAD_FAILED)
    } finally {
      loading.value = false
    }
  }

  function clearSelection(): void {
    selectedIds.value = []
  }

  function reloadFromFirstPage(): void {
    page.value = 1
    clearSelection()
    void load()
  }

  function setStatus(next: OpsStatusFilter): void {
    if (status.value === next) return
    status.value = next
    reloadFromFirstPage()
  }

  function goPage(next: number): void {
    const target = Math.max(1, Math.min(next, totalPages.value))
    if (target === page.value) return
    page.value = target
    clearSelection()
    void load()
  }

  function setSelected(ids: number[]): void {
    selectedIds.value = [...ids]
  }

  function toggleSelected(id: number, checked: boolean): void {
    if (checked) {
      if (!selectedIds.value.includes(id)) selectedIds.value = [...selectedIds.value, id]
      return
    }
    selectedIds.value = selectedIds.value.filter((item) => item !== id)
  }

  let timer: ReturnType<typeof setTimeout> | null = null
  watch(keyword, () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      reloadFromFirstPage()
    }, OPS_KEYWORD_DEBOUNCE_MS)
  })

  return {
    users,
    total,
    page,
    keyword,
    status,
    loading,
    loaded,
    error,
    selectedIds,
    totalPages,
    showEmpty,
    load,
    setStatus,
    goPage,
    toggleSelected,
    setSelected,
    clearSelection,
  }
}
