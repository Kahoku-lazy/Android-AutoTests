import { ref } from "vue"
import type { Ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { createLogPort, deleteLogPort, updateLogPort } from "../api"
import type { LogPortRow } from "../api"
import { validatePortForm } from "../helpers/port-form"
import type { PortFormPayload } from "../helpers/port-form"
import { PORT_DELETE_CONFIRM, PORT_DELETE_TITLE, PORT_DELETE_WARNING } from "../constants"
import { formatApiError } from "@/shared/api-client"

export function useCustomPorts(ports: Ref<LogPortRow[]>, reload: () => Promise<void>) {
  const dialogVisible = ref(false)
  const editRow = ref<LogPortRow | null>(null)
  const saving = ref(false)
  const formError = ref("")

  function openAdd(): void {
    editRow.value = null
    formError.value = ""
    dialogVisible.value = true
  }

  function openEdit(row: LogPortRow): void {
    editRow.value = row
    formError.value = ""
    dialogVisible.value = true
  }

  function closeDialog(): void {
    dialogVisible.value = false
    formError.value = ""
  }

  async function submit(payload: PortFormPayload): Promise<void> {
    if (saving.value) return
    const editing = editRow.value
    const check = validatePortForm(
      {
        portText: String(payload.port),
        sku: payload.sku,
        baudChoice: payload.baud,
        baudCustomText: "",
      },
      {
        editMode: editing !== null,
        editPort: editing?.port,
        existingPorts: ports.value.map((row) => row.port),
      },
    )
    if (check.kind === "error") {
      formError.value = check.error
      return
    }
    saving.value = true
    formError.value = ""
    try {
      const res = editing
        ? await updateLogPort(editing.port, { sku: check.payload.sku, baud: check.payload.baud })
        : await createLogPort(check.payload)
      if (res.status && res.data) {
        const row = res.data
        closeDialog()
        await reload()
        if (row.enabled && !row.listening) {
          ElMessage.error(row.note || `端口 ${row.port} 监听失败`)
        } else {
          ElMessage.success(
            editing ? `端口 ${row.port} 已更新` : `端口 ${row.port} 已新增并开始监听`,
          )
        }
      } else {
        formError.value = res.message || "操作失败"
      }
    } catch (e) {
      formError.value = formatApiError(e, "操作失败")
    } finally {
      saving.value = false
    }
  }

  async function remove(row: LogPortRow): Promise<void> {
    try {
      await ElMessageBox.confirm(PORT_DELETE_WARNING, PORT_DELETE_TITLE, {
        type: "warning",
        confirmButtonText: PORT_DELETE_CONFIRM,
        cancelButtonText: "取消",
      })
    } catch {
      return
    }
    try {
      const res = await deleteLogPort(row.port)
      if (res.status) {
        ElMessage.success(res.data?.note || `端口 ${row.port} 已删除`)
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
