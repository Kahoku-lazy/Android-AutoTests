/** useDevicePrompts — 设备控制三角色系统提示词读写 + 历史存档（自动档滚动三份 / 永久档唯一）
 *
 *  编辑与保存按角色独立：某一份进入编辑 / 保存 / 取消 MUST NOT 改变其余份的编辑态与草稿。
 *  写库载荷一律以「当前已保存值」为基底，只覆盖被保存（或退出编辑时仍有改动）的那几份，
 *  因此另一份尚未保存的草稿不会被带进库。
 */
import { ref, reactive, onMounted } from "vue"
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
import { PROMPT_OVERWRITE_CONFIRM, PROMPT_ROLES, promptRoleLabel } from "../constants"
import type { PromptRole } from "../constants"
import { formatApiError } from "@/shared/api-client"

const EMPTY: DevicePrompts = { planner: "", executor: "", verifier: "" }

type PromptPayload = { planner: string; executor: string; verifier: string }

export function useDevicePrompts() {
  const prompts = ref<DevicePrompts>({ ...EMPTY })
  const draft = ref<DevicePrompts>({ ...EMPTY })
  const loading = ref(false)
  const saving = ref(false)
  /** 按角色编辑态：多份可同时为 true，互不影响 */
  const editingRoles = reactive<Record<PromptRole, boolean>>({
    planner: false,
    executor: false,
    verifier: false,
  })

  const archives = ref<DevicePromptArchive[]>([])
  const archivesLoading = ref(false)
  const historyVisible = ref(false)
  const preview = ref<DevicePromptArchive | null>(null)

  function _savedPayload(): PromptPayload {
    return {
      planner: prompts.value.planner || "",
      executor: prompts.value.executor || "",
      verifier: prompts.value.verifier || "",
    }
  }

  /** 写库载荷：以已保存值为基底，只覆盖 overrides 点名的份 */
  function _mergePayload(overrides: Partial<Record<PromptRole, string>>): PromptPayload {
    return { ..._savedPayload(), ...overrides }
  }

  /**
   * 用一次接口结果刷新状态。
   * resetRoles 省略 = 整体重置（读取 / 覆盖存档）；给出时只重置这几份的草稿，
   * 保留其余编辑中份尚未保存的内容。
   */
  function _apply(data?: DevicePrompts, resetRoles?: PromptRole[]): void {
    prompts.value = {
      planner: data?.planner || "",
      executor: data?.executor || "",
      verifier: data?.verifier || "",
      agent_id: data?.agent_id,
    }
    if (!resetRoles) {
      draft.value = { ...prompts.value }
      return
    }
    const next: DevicePrompts = { ...draft.value }
    for (const role of resetRoles) next[role] = prompts.value[role] || ""
    draft.value = next
  }

  function _clearEditing(): void {
    for (const item of PROMPT_ROLES) editingRoles[item.key] = false
  }

  function isEditing(role: PromptRole): boolean {
    return editingRoles[role]
  }

  function isDirty(role: PromptRole): boolean {
    return (draft.value[role] || "") !== (prompts.value[role] || "")
  }

  /** 处于编辑态且与库中值不同的份 = 退出编辑自动保存的候选集 */
  function dirtyRoles(): PromptRole[] {
    return PROMPT_ROLES.map((item) => item.key).filter((key) => isEditing(key) && isDirty(key))
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

  /** 进入某一份编辑：只重置该份草稿为库中值并置其编辑态，其余份不受影响。 */
  function startEdit(role: PromptRole): void {
    draft.value = { ...draft.value, [role]: prompts.value[role] || "" }
    editingRoles[role] = true
  }

  /**
   * 退出编辑自动保存：只写「编辑中且有改动」的份（给 roles 时只处理这几份），
   * 一次合并提交；无改动 MUST NOT 写库。
   */
  async function autoSaveIfDirty(roles?: PromptRole[]): Promise<boolean> {
    const dirty = dirtyRoles().filter((role) => !roles || roles.includes(role))
    if (!dirty.length) return false
    const overrides: Partial<Record<PromptRole, string>> = {}
    for (const role of dirty) overrides[role] = draft.value[role] || ""
    try {
      const data = await updateDevicePrompts(_mergePayload(overrides), "auto")
      if (!data.status) {
        ElMessage.error(data.message || "自动保存失败")
        return false
      }
      _apply(data.data, dirty)
      return true
    } catch (e) {
      ElMessage.error(formatApiError(e, "自动保存失败"))
      return false
    }
  }

  /** 退出某一份编辑：只处理该份（有改动才自动落库），其余份的草稿与编辑态不受影响。 */
  async function cancelEdit(role: PromptRole): Promise<void> {
    await autoSaveIfDirty([role])
    draft.value = { ...draft.value, [role]: prompts.value[role] || "" }
    editingRoles[role] = false
  }

  /** 保存某一份：只提交该份新正文，其余两份取当前已保存值（不带入其余份未保存的草稿）。 */
  async function save(role: PromptRole): Promise<boolean> {
    const text = draft.value[role] || ""
    if (!text.trim()) {
      ElMessage.error(promptRoleLabel(role) + " 系统提示词不能为空")
      return false
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
      const data = await updateDevicePrompts(_mergePayload({ [role]: text }), "permanent")
      if (!data.status) {
        ElMessage.error(data.message || "保存失败")
        return false
      }
      _apply(data.data, [role])
      editingRoles[role] = false
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
      _clearEditing()
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
    editingRoles,
    isEditing,
    startEdit,
    cancelEdit,
    save,
    autoSaveIfDirty,
    load,
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
