/**
 * 用户管理列表的状态与流程：服务端分页、关键字防抖、状态筛选。
 *
 * 业务：
 * - 首次加载由页面在挂载时调用 `load()`（本组合式不接管生命周期）
 * - 改筛选条件回到第 1 页
 * - 关键字输入防抖，避免每敲一个字发一次请求
 * - 加载期保留旧数据（不清空表格），失败时给出可重试的错误文案
 */
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
  const pageSize = ref(OPS_DEFAULT_PAGE_SIZE)
  const keyword = ref("")
  const status = ref<OpsStatusFilter>("all")
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref("")

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const showEmpty = computed(() => loaded.value && !loading.value && users.value.length === 0)

  async function load(): Promise<void> {
    loading.value = true
    error.value = ""
    try {
      const { data } = await listOpsUsers({
        page: page.value,
        page_size: pageSize.value,
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

  /** 换筛选条件后回到第 1 页再拉，避免停在第 N 页拿到空片。 */
  function reloadFromFirstPage(): void {
    page.value = 1
    void load()
  }

  function setStatus(next: OpsStatusFilter): void {
    if (status.value === next) return
    status.value = next
    reloadFromFirstPage()
  }

  function setPageSize(size: number): void {
    pageSize.value = size
    reloadFromFirstPage()
  }

  function goPage(next: number): void {
    const target = Math.max(1, Math.min(next, totalPages.value))
    if (target === page.value) return
    page.value = target
    void load()
  }

  // 关键字防抖：连打不连发
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
    pageSize,
    keyword,
    status,
    loading,
    loaded,
    error,
    totalPages,
    showEmpty,
    load,
    setStatus,
    setPageSize,
    goPage,
  }
}
