import { ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { createLogKeyword, deleteLogKeyword, updateLogKeyword } from "../api"
import type { LogKeywordRow } from "../helpers/log-keyword-rows"
import { validateKeywordForm } from "../helpers/keyword-form"
import type { KeywordFormPayload } from "../helpers/keyword-form"
import { KEYWORD_DELETE_CONFIRM, KEYWORD_DELETE_TITLE, KEYWORD_DELETE_WARNING } from "../constants"
import { formatApiError } from "@/shared/api-client"

export function useKeywordCrud(reload: () => Promise<void>) {
  const dialogVisible = ref(false)
  const editRow = ref<LogKeywordRow | null>(null)
  const saving = ref(false)
  const formError = ref("")

  function openAdd(): void {
    editRow.value = null
    formError.value = ""
    dialogVisible.value = true
  }

  function openEdit(row: LogKeywordRow): void {
    editRow.value = row
    formError.value = ""
    dialogVisible.value = true
  }

  function closeDialog(): void {
    dialogVisible.value = false
    formError.value = ""
  }

  async function submit(payload: KeywordFormPayload): Promise<void> {
    if (saving.value) return
    const editing = editRow.value
    const check = validateKeywordForm({
      keyword: payload.keyword,
      module: payload.module,
      feature: payload.feature,
      scope: payload.scope,
      featureIdText: payload.feature_id !== undefined ? String(payload.feature_id) : "",
    })
    if (check.kind === "error") {
      formError.value = check.error
      return
    }
    saving.value = true
    formError.value = ""
    try {
      const res = editing
        ? await updateLogKeyword(editing.rowId as number, check.payload)
        : await createLogKeyword(check.payload)
      if (res.status && res.data) {
        closeDialog()
        await reload()
        ElMessage.success(editing ? "关键词已更新" : "关键词已新建")
      } else {
        formError.value = res.message || "操作失败"
      }
    } catch (e) {
      formError.value = formatApiError(e, "操作失败")
    } finally {
      saving.value = false
    }
  }

  async function remove(row: LogKeywordRow): Promise<void> {
    try {
      await ElMessageBox.confirm(KEYWORD_DELETE_WARNING, KEYWORD_DELETE_TITLE, {
        type: "warning",
        confirmButtonText: KEYWORD_DELETE_CONFIRM,
        cancelButtonText: "取消",
      })
    } catch {
      return
    }
    try {
      const res = await deleteLogKeyword(row.rowId as number)
      if (res.status) {
        ElMessage.success(res.data?.note || "关键词已删除")
        await reload()
      } else {
        ElMessage.error(res.message || "删除失败")
      }
    } catch (e) {
      ElMessage.error(formatApiError(e, "删除失败"))
    }
  }

  return {
    dialogVisible,
    editRow,
    saving,
    formError,
    openAdd,
    openEdit,
    closeDialog,
    submit,
    remove,
  }
}
