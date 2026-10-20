/** useCaseSheet — Excel 多行用例加载 / 新建行 / 保存 / 删除 */
import { computed, ref, watch } from "vue"
import { onBeforeRouteLeave } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import {
  createDefinition,
  deleteDefinition,
  getFileSheet,
  updateDefinition,
  updateFile,
} from "../api"
import { MAX_STEP_TEXT } from "../types"
import type { CaseDefinition, CaseFileMeta, CaseStep, SheetRowDraft } from "../types"

let tempSeq = 0

export function emptySheetRow(): SheetRowDraft {
  tempSeq += 1
  return {
    id: `temp-${Date.now()}-${tempSeq}`,
    title: "",
    priority: "P1",
    system: "ANDROID",
    case_type: "AUTO",
    business_type: "appliance",
    module: "",
    precondition: "",
    steps: [],
    updated_at: "",
    dirty: true,
    isNew: true,
  }
}

function toSteps(steps: CaseStep[] | undefined): CaseStep[] {
  return (steps || []).map((step) => ({ action: step.action, assertion: step.assertion }))
}

function toDraft(row: CaseDefinition): SheetRowDraft {
  return {
    id: row.id,
    title: row.title,
    priority: row.priority,
    system: row.system,
    case_type: row.case_type,
    business_type: row.business_type,
    module: row.module,
    precondition: row.precondition,
    steps: toSteps(row.steps),
    updated_at: row.updated_at,
    dirty: false,
    isNew: false,
  }
}

export function validateRow(row: SheetRowDraft): string | null {
  if (!row.title.trim()) return "测试标题不能为空"
  if (!row.steps.length) return "执行步骤不能为空"
  for (const [index, step] of row.steps.entries()) {
    if (!step.action.trim()) return `第 ${index + 1} 步：动作不能为空`
    if (!step.assertion.trim()) return `第 ${index + 1} 步：断言不能为空`
    if (step.action.length > MAX_STEP_TEXT) return `第 ${index + 1} 步：动作不能超过 ${MAX_STEP_TEXT} 字符`
    if (step.assertion.length > MAX_STEP_TEXT)
      return `第 ${index + 1} 步：断言不能超过 ${MAX_STEP_TEXT} 字符`
  }
  return null
}

export function useCaseSheet(projectId: () => number, fileId: () => number) {
  const fileMeta = ref<CaseFileMeta | null>(null)
  const rows = ref<SheetRowDraft[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const skipGuard = ref(false)

  const isDirty = computed(() => rows.value.some((r) => r.dirty))
  const dirtyCount = computed(() => rows.value.filter((r) => r.dirty).length)

  /** 行号前缀：服务端只报步骤序号，行号由前端补 */
  function rowLabel(row: SheetRowDraft): string {
    const index = rows.value.findIndex((r) => r.id === row.id)
    return index >= 0 ? `第 ${index + 1} 行` : "当前行"
  }

  async function loadSheet() {
    const fid = fileId()
    if (!fid) return
    loading.value = true
    error.value = null
    try {
      const { data } = await getFileSheet(fid)
      if (data.status && data.data) {
        fileMeta.value = data.data.file
        rows.value = (data.data.rows || []).map(toDraft)
      } else {
        error.value = data.message || "表格加载失败"
      }
    } catch (e: unknown) {
      error.value = formatApiError(e, "表格加载失败")
    } finally {
      loading.value = false
    }
  }

  function markDirty(row: SheetRowDraft) {
    row.dirty = true
  }

  function applySteps(row: SheetRowDraft, steps: CaseStep[]) {
    row.steps = toSteps(steps)
    markDirty(row)
  }

  function addRow() {
    rows.value.push(emptySheetRow())
  }

  async function renameSheet(name: string) {
    const fid = fileId()
    try {
      const { data } = await updateFile(fid, { name: name.trim() })
      if (data.status && data.data) {
        fileMeta.value = data.data
        ElMessage.success("文件名已更新")
        return true
      }
      ElMessage.error(data.message || "重命名失败")
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, "重命名失败"))
      return false
    }
  }

  async function saveAll() {
    const dirtyRows = rows.value.filter((r) => r.dirty)
    if (!dirtyRows.length) {
      ElMessage.info("没有需要保存的修改")
      return true
    }
    for (const row of dirtyRows) {
      const msg = validateRow(row)
      if (msg) {
        ElMessage.warning(`${rowLabel(row)} · ${msg}`)
        return false
      }
    }

    saving.value = true
    try {
      const pid = projectId()
      const fid = fileId()
      for (const row of dirtyRows) {
        const body = {
          title: row.title.trim(),
          priority: row.priority,
          system: row.system,
          case_type: row.case_type,
          business_type: row.business_type,
          module: row.module.trim(),
          precondition: row.precondition,
          steps: toSteps(row.steps),
        }
        if (row.isNew) {
          const { data } = await createDefinition({
            project_id: pid,
            file_id: fid,
            ...body,
            sort_order: rows.value.indexOf(row),
          })
          if (!data.status || !data.data) {
            ElMessage.error(`${rowLabel(row)} · ${data.message || "新建行失败"}`)
            return false
          }
          const idx = rows.value.findIndex((r) => r.id === row.id)
          if (idx >= 0) rows.value[idx] = toDraft(data.data)
        } else {
          const { data } = await updateDefinition(row.id, body)
          if (!data.status || !data.data) {
            ElMessage.error(`${rowLabel(row)} · ${data.message || "保存失败"}`)
            return false
          }
          const idx = rows.value.findIndex((r) => r.id === row.id)
          if (idx >= 0) rows.value[idx] = toDraft(data.data)
        }
      }
      ElMessage.success("已保存")
      return true
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, "保存失败"))
      return false
    } finally {
      saving.value = false
    }
  }

  async function removeRow(row: SheetRowDraft) {
    if (row.isNew) {
      rows.value = rows.value.filter((r) => r.id !== row.id)
      return
    }
    try {
      await ElMessageBox.confirm(`确认删除用例「${row.title || row.id}」？`, "确认删除", {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      })
    } catch {
      return
    }
    try {
      const { data } = await deleteDefinition(row.id)
      if (data.status) {
        rows.value = rows.value.filter((r) => r.id !== row.id)
        ElMessage.success("已删除")
      } else {
        ElMessage.error(data.message || "删除失败")
      }
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, "删除失败"))
    }
  }

  onBeforeRouteLeave(async () => {
    if (skipGuard.value || !isDirty.value) return true
    try {
      await ElMessageBox.confirm("有未保存的修改，确定离开？", "提示", {
        confirmButtonText: "离开",
        cancelButtonText: "留下",
        type: "warning",
      })
      return true
    } catch {
      return false
    }
  })

  watch(
    () => fileId(),
    () => {
      void loadSheet()
    },
    { immediate: true },
  )

  return {
    fileMeta,
    rows,
    loading,
    saving,
    error,
    isDirty,
    dirtyCount,
    skipGuard,
    loadSheet,
    markDirty,
    applySteps,
    addRow,
    saveAll,
    removeRow,
    renameSheet,
  }
}
