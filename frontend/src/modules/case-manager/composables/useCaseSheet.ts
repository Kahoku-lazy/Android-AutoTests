/** useCaseSheet — Excel 多行用例加载 / 新建行 / 保存 / 删除 */
import { computed, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import {
  createDefinition,
  deleteDefinition,
  getFileSheet,
  updateDefinition,
  updateFile,
} from '../api'
import type {
  BusinessType,
  CaseDefinition,
  CaseFileMeta,
  SheetRowDraft,
  TestType,
} from '../types'

let tempSeq = 0

export function emptySheetRow(): SheetRowDraft {
  tempSeq += 1
  return {
    id: `temp-${Date.now()}-${tempSeq}`,
    title: '',
    test_type: 'app',
    business_type: 'appliance',
    module: '',
    precondition: '',
    steps: '',
    expected_result: '',
    updated_at: '',
    dirty: true,
    isNew: true,
  }
}

function toDraft(row: CaseDefinition): SheetRowDraft {
  return {
    id: row.id,
    title: row.title,
    test_type: row.test_type,
    business_type: row.business_type,
    module: row.module,
    precondition: row.precondition,
    steps: row.steps,
    expected_result: row.expected_result,
    updated_at: row.updated_at,
    dirty: false,
    isNew: false,
  }
}

function validateRow(row: SheetRowDraft): string | null {
  if (!row.title.trim()) return '测试标题不能为空'
  if (!row.steps.trim()) return '执行步骤不能为空'
  if (!row.expected_result.trim()) return '预期结果不能为空'
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
        error.value = data.message || '表格加载失败'
      }
    } catch (e: unknown) {
      error.value = formatApiError(e, '表格加载失败')
    } finally {
      loading.value = false
    }
  }

  function markDirty(row: SheetRowDraft) {
    row.dirty = true
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
        ElMessage.success('文件名已更新')
        return true
      }
      ElMessage.error(data.message || '重命名失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '重命名失败'))
      return false
    }
  }

  async function saveAll() {
    const dirtyRows = rows.value.filter((r) => r.dirty)
    if (!dirtyRows.length) {
      ElMessage.info('没有需要保存的修改')
      return true
    }
    for (const row of dirtyRows) {
      const msg = validateRow(row)
      if (msg) {
        ElMessage.warning(msg)
        return false
      }
    }

    saving.value = true
    try {
      const pid = projectId()
      const fid = fileId()
      for (let i = 0; i < dirtyRows.length; i++) {
        const row = dirtyRows[i]
        const body = {
          title: row.title.trim(),
          test_type: row.test_type as TestType,
          business_type: row.business_type as BusinessType,
          module: row.module.trim(),
          precondition: row.precondition,
          steps: row.steps,
          expected_result: row.expected_result,
          require_fields: true,
        }
        if (row.isNew) {
          const { data } = await createDefinition({
            project_id: pid,
            file_id: fid,
            ...body,
            sort_order: rows.value.indexOf(row),
          })
          if (!data.status || !data.data) {
            ElMessage.error(data.message || '新建行失败')
            return false
          }
          const idx = rows.value.findIndex((r) => r.id === row.id)
          if (idx >= 0) rows.value[idx] = toDraft(data.data)
        } else {
          const { data } = await updateDefinition(row.id, body)
          if (!data.status || !data.data) {
            ElMessage.error(data.message || '保存失败')
            return false
          }
          const idx = rows.value.findIndex((r) => r.id === row.id)
          if (idx >= 0) rows.value[idx] = toDraft(data.data)
        }
      }
      ElMessage.success('已保存')
      return true
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '保存失败'))
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
      await ElMessageBox.confirm(`确认删除用例「${row.title || row.id}」？`, '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
    try {
      const { data } = await deleteDefinition(row.id)
      if (data.status) {
        rows.value = rows.value.filter((r) => r.id !== row.id)
        ElMessage.success('已删除')
      } else {
        ElMessage.error(data.message || '删除失败')
      }
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '删除失败'))
    }
  }

  onBeforeRouteLeave(async () => {
    if (skipGuard.value || !isDirty.value) return true
    try {
      await ElMessageBox.confirm('有未保存的修改，确定离开？', '提示', {
        confirmButtonText: '离开',
        cancelButtonText: '留下',
        type: 'warning',
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
    addRow,
    saveAll,
    removeRow,
    renameSheet,
  }
}
