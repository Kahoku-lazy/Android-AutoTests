/** useDevicePrompts — 设备控制三角色系统提示词读写 + 历史存档（自动档滚动三份 / 永久档唯一） */
import { ref, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import {
  fetchDevicePrompts,
  updateDevicePrompts,
  fetchDevicePromptArchives,
  fetchDevicePromptArchive,
  deleteDevicePromptArchive,
  restoreDevicePromptArchive,
  type DevicePrompts,
  type DevicePromptArchive,
} from "../api/toolbox"
import { PROMPT_OVERWRITE_CONFIRM } from "../constants"
import { formatApiError } from "@/shared/api-client"

const EMPTY: DevicePrompts = { planner: "", executor: "", verifier: "" }

function samePrompts(a: DevicePrompts, b: DevicePrompts): boolean {
  return a.planner === b.planner && a.executor === b.executor && a.verifier === b.verifier
}

export function useDevicePrompts() {
  const prompts = ref<DevicePrompts>({ ...EMPTY })
  const draft = ref<DevicePrompts>({ ...EMPTY })
  const loading = ref(false)
  const saving = ref(false)
  const editing = ref(false)

  const archives = ref<DevicePromptArchive[]>([])
  const archivesLoading = ref(false)
  const historyVisible = ref(false)
  const preview = ref<DevicePromptArchive | null>(null)

  function _apply(data?: DevicePrompts): void {
    prompts.value = {
      planner: data?.planner || "",
      executor: data?.executor || "",
      verifier: data?.verifier || "",
      agent_id: data?.agent_id,
    }
    draft.value = { ...prompts.value }
  }

  async function load() {
    loading.value = true
    try {
      const data = await fetchDevicePrompts()
      if (data.status && data.data) _apply(data.data)
    } catch (e) {
      ElMessage.error(formatApiError(e, "提示词加载失败"))
    }
    loading.value = false
  }

  function startEdit() {
    draft.value = { ...prompts.value }
    editing.value = true
  }

  /** 退出编辑：有改动才自动写库并留一份自动档；无改动什么都不做。 */
  async function autoSaveIfDirty(): Promise<boolean> {
    if (samePrompts(draft.value, prompts.value)) return false
    try {
      const data = await updateDevicePrompts(draft.value, "auto")
      if (!data.status) {
        ElMessage.error(data.message || "自动保存失败")
        return false
      }
      _apply(data.data)
      return true
    } catch (e) {
      ElMessage.error(formatApiError(e, "自动保存失败"))
      return false
    }
  }

  async function cancelEdit(): Promise<void> {
    await autoSaveIfDirty()
    draft.value = { ...prompts.value }
    editing.value = false
  }

  /** 手工保存：会覆盖唯一永久存档，所以 MUST 先让用户确认。 */
  async function save(): Promise<boolean> {
    const payload = {
      planner: draft.value.planner || "",
      executor: draft.value.executor || "",
      verifier: draft.value.verifier || "",
    }
    for (const [role, text] of Object.entries(payload) as [keyof typeof payload, string][]) {
      if (!text.trim()) {
        ElMessage.error(role + " 系统提示词不能为空")
        return false
      }
    }
    try {
      await ElMessageBox.confirm(PROMPT_OVERWRITE_CONFIRM, "确认保存", {
        type: "warning",
        confirmButtonText: "覆盖保存",
        cancelButtonText: "取消",
      })
    } catch {
      return false // 取消：不写库、不动任何存档
    }
    saving.value = true
    try {
      const data = await updateDevicePrompts(payload, "permanent")
      if (!data.status) {
        ElMessage.error(data.message || "保存失败")
        return false
      }
      _apply(data.data)
      editing.value = false
      ElMessage.success("提示词已保存")
      if (historyVisible.value) await loadArchives()
      return true
    } catch (e) {
      ElMessage.error(formatApiError(e, "保存失败"))
      return false
    } finally {
      saving.value = false
    }
  }

  // ── 历史存档 ──

  async function loadArchives(): Promise<void> {
    archivesLoading.value = true
    try {
      const data = await fetchDevicePromptArchives()
      if (data.status) archives.value = data.data?.items || []
    } catch (e) {
      ElMessage.error(formatApiError(e, "历史记录加载失败"))
    }
    archivesLoading.value = false
  }

  async function openHistory(): Promise<void> {
    historyVisible.value = true
    preview.value = null
    await loadArchives()
  }

  async function previewArchive(id: number): Promise<void> {
    try {
      const data = await fetchDevicePromptArchive(id)
      if (data.status) preview.value = data.data || null
    } catch (e) {
      ElMessage.error(formatApiError(e, "存档读取失败"))
    }
  }

  /** 用历史存档覆盖当前提示词：服务端会先把当前值留成自动档再覆盖。 */
  async function restoreArchive(id: number): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        "用该存档覆盖当前提示词？覆盖前会自动把当前提示词留成一份自动存档。",
        "确认覆盖",
        { type: "warning", confirmButtonText: "覆盖当前", cancelButtonText: "取消" },
      )
    } catch {
      return false
    }
    try {
      const data = await restoreDevicePromptArchive(id)
      if (!data.status) {
        ElMessage.error(data.message || "覆盖失败")
        return false
      }
      _apply(data.data)
      editing.value = false
      ElMessage.success("已用历史存档覆盖当前提示词")
      await loadArchives()
      return true
    } catch (e) {
      ElMessage.error(formatApiError(e, "覆盖失败"))
      return false
    }
  }

  /** 删除永久存档（自动档由滚动淘汰管理，不提供删除入口）。 */
  async function removePermanentArchive(id: number): Promise<boolean> {
    try {
      await ElMessageBox.confirm("确定删除这份永久存档吗？删除后不可恢复。", "确认删除", {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      })
    } catch {
      return false
    }
    try {
      const data = await deleteDevicePromptArchive(id)
      if (!data.status) {
        ElMessage.error(data.message || "删除失败")
        return false
      }
      ElMessage.success("永久存档已删除")
      if (preview.value?.id === id) preview.value = null
      await loadArchives()
      return true
    } catch (e) {
      ElMessage.error(formatApiError(e, "删除失败"))
      return false
    }
  }

  onMounted(load)

  return {
    prompts,
    draft,
    loading,
    saving,
    editing,
    load,
    startEdit,
    cancelEdit,
    save,
    autoSaveIfDirty,
    archives,
    archivesLoading,
    historyVisible,
    preview,
    openHistory,
    loadArchives,
    previewArchive,
    restoreArchive,
    removePermanentArchive,
  }
}
