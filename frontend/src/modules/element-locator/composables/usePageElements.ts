/**
 * 元素行工作台状态：列表加载、每页 10 行分页、行勾选、单格更新、新增与批量删除。
 * 组件只做渲染与事件绑定；校验规则在 helpers/elementRowValidation.ts。
 *
 * 行字段按收敛口径（缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点）：
 * 只有元素名称、文本、主定位与测试点可写，其余为采集产物（只读）。
 */
import { computed, ref, watch } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { usePagination } from "@/shared/composables/usePagination"
import { apiPageItems, apiUpdateElement, batchDeleteElements, createPageElement } from "../api"
import type { PageElementFields } from "../api"
import type { PageElementPayload } from "../types"

/** 接口一次取回上限（后端既有约束）；本地分页在这份集合上切页 */
const FETCH_LIMIT = 500
/** 每页固定 10 行，不提供行数选择器 */
const PAGE_SIZE = 10

/** 行内可编辑字段（与后端 UPDATE_FIELDS 同源） */
export type EditableField = "alias" | "text_val" | "primary_xpath" | "is_test_point"

export interface PageElementRow {
  id: number
  alias: string
  seq: number
  text_val: string
  primary_xpath: string
  thumbnail_path: string
  is_test_point: boolean
  clickable: boolean
  long_clickable: boolean
  scrollable: boolean
  checkable: boolean
  checked: boolean
  enabled: boolean
  focusable: boolean
}

function toRow(raw: PageElementPayload): PageElementRow {
  return {
    id: Number(raw.id),
    alias: String(raw.alias || ""),
    seq: Number(raw.seq) || 0,
    text_val: String(raw.text_val || ""),
    primary_xpath: String(raw.primary_xpath || ""),
    thumbnail_path: String(raw.thumbnail_path || ""),
    is_test_point: Boolean(raw.is_test_point),
    clickable: Boolean(raw.clickable),
    long_clickable: Boolean(raw.long_clickable),
    scrollable: Boolean(raw.scrollable),
    checkable: Boolean(raw.checkable),
    checked: Boolean(raw.checked),
    enabled: Boolean(raw.enabled),
    focusable: Boolean(raw.focusable),
  }
}

export function usePageElements(pageId: () => number) {
  const loading = ref(false)
  const error = ref("")
  const rows = ref<PageElementRow[]>([])
  const total = ref(0)
  const selectedIds = ref<number[]>([])

  const { currentPage, totalPages, pagedItems, goPage } = usePagination(rows, {
    pageSize: PAGE_SIZE,
  })

  /** 接口一次只取回 FETCH_LIMIT 条：超出时如实提示，不假装是全部 */
  const truncated = computed(() => total.value > rows.value.length)

  const allSelectedOnPage = computed(
    () => pagedItems.value.length > 0 && pagedItems.value.every((row) => isSelected(row.id)),
  )

  function isSelected(id: number): boolean {
    return selectedIds.value.includes(id)
  }

  function toggleRow(id: number) {
    selectedIds.value = isSelected(id)
      ? selectedIds.value.filter((item) => item !== id)
      : [...selectedIds.value, id]
  }

  function toggleAllOnPage(checked: boolean) {
    const pageIds = pagedItems.value.map((row) => row.id)
    selectedIds.value = checked
      ? Array.from(new Set([...selectedIds.value, ...pageIds]))
      : selectedIds.value.filter((id) => !pageIds.includes(id))
  }

  /**
   * 拉取该页元素。`keepSelection` 只用于「更新失败后用服务端数据对齐」：
   * 那次重载与用户的勾选意图无关，不能连带把勾选清掉（只保留仍然存在的 id）。
   */
  async function load(options: { keepSelection?: boolean } = {}) {
    loading.value = true
    error.value = ""
    try {
      const { data } = await apiPageItems(pageId(), "all", FETCH_LIMIT)
      if (data.status) {
        rows.value = (data.elements || []).map(toRow)
        total.value = Number(data.total ?? rows.value.length)
        if (options.keepSelection) {
          const alive = new Set(rows.value.map((row) => row.id))
          selectedIds.value = selectedIds.value.filter((id) => alive.has(id))
        } else {
          selectedIds.value = []
        }
      } else {
        error.value = data.message || "页面元素加载失败"
        rows.value = []
        total.value = 0
      }
    } catch (e: unknown) {
      error.value = formatApiError(e as never, "加载失败")
      rows.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  function applyLocal(row: PageElementRow, field: EditableField, value: string | boolean) {
    if (field === "is_test_point") {
      row.is_test_point = Boolean(value)
      return
    }
    row[field] = String(value)
  }

  /** 单格更新：成功后只更新本地该行；失败则重载，保证界面与服务端一致 */
  async function updateField(
    row: PageElementRow,
    field: EditableField,
    value: string | boolean,
  ): Promise<boolean> {
    const payload: PageElementFields = {}
    if (field === "is_test_point") payload.is_test_point = Boolean(value)
    else payload[field] = String(value)

    try {
      const { data } = await apiUpdateElement(row.id, payload)
      if (!data.status) {
        ElMessage.error(data.message || "更新失败")
        await load({ keepSelection: true })
        return false
      }
      applyLocal(row, field, value)
      return true
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e as never, "更新失败"))
      await load({ keepSelection: true })
      return false
    }
  }

  async function createRow(fields: PageElementFields): Promise<boolean> {
    try {
      const { data } = await createPageElement(pageId(), fields)
      if (!data.status) {
        ElMessage.error(data.message || "新增失败")
        return false
      }
      ElMessage.success("已新增一行")
      await load()
      goPage(totalPages.value)
      return true
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e as never, "新增失败"))
      return false
    }
  }

  async function removeSelected(): Promise<boolean> {
    if (!selectedIds.value.length) {
      ElMessage.warning("请先勾选要删除的行")
      return false
    }
    try {
      const { data } = await batchDeleteElements(selectedIds.value)
      if (!data.status) {
        ElMessage.error(data.message || "删除失败")
        return false
      }
      ElMessage.success(`已删除 ${data.data?.deleted ?? selectedIds.value.length} 行`)
      selectedIds.value = []
      await load()
      return true
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e as never, "删除失败"))
      return false
    }
  }

  watch(
    pageId,
    () => {
      void load()
    },
    { immediate: true },
  )

  return {
    loading,
    error,
    rows,
    total,
    truncated,
    currentPage,
    totalPages,
    pagedItems,
    goPage,
    selectedIds,
    allSelectedOnPage,
    isSelected,
    toggleRow,
    toggleAllOnPage,
    load,
    updateField,
    createRow,
    removeSelected,
  }
}
