/** usePrototypes — 页面流原型列表与创建 */
import { ref, computed } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import {
  createWorkflowPrototype,
  deleteWorkflowPrototype,
  listWorkflowPrototypes,
  type WorkflowPrototype,
} from "../api"

export type { WorkflowPrototype }

export function usePrototypes() {
  const prototypes = ref<WorkflowPrototype[]>([])
  const loading = ref(false)
  const creating = ref(false)
  const error = ref<string | null>(null)

  const isEmpty = computed(() => !loading.value && prototypes.value.length === 0)

  async function loadPrototypes() {
    loading.value = true
    error.value = null
    try {
      const { data } = await listWorkflowPrototypes()
      if (data.status && Array.isArray(data.data)) {
        prototypes.value = data.data
      } else {
        prototypes.value = []
        error.value = data.message || "原型列表加载失败"
      }
    } catch (e: unknown) {
      prototypes.value = []
      error.value = formatApiError(e, "原型列表加载失败")
    } finally {
      loading.value = false
    }
  }

  async function addPrototype(name: string, description = "") {
    const trimmed = name.trim()
    if (!trimmed) {
      ElMessage.warning("请输入原型名称")
      return null
    }
    creating.value = true
    try {
      const { data } = await createWorkflowPrototype({
        name: trimmed,
        description: description.trim(),
      })
      // 集合路由返回标准信封 {status, data: 原型}
      if (data.status && data.data) {
        prototypes.value = [data.data, ...prototypes.value]
        ElMessage.success("原型已创建")
        return data.data as WorkflowPrototype
      }
      ElMessage.error(data.message || "创建失败")
      return null
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, "创建失败"))
      return null
    } finally {
      creating.value = false
    }
  }

  async function removePrototype(id: number) {
    try {
      const { data } = await deleteWorkflowPrototype(id)
      if (data.status) {
        prototypes.value = prototypes.value.filter((p) => p.id !== id)
        ElMessage.success("原型已删除")
        return true
      }
      ElMessage.error(data.message || "删除失败")
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, "删除失败"))
      return false
    }
  }

  return {
    prototypes,
    loading,
    creating,
    error,
    isEmpty,
    loadPrototypes,
    addPrototype,
    removePrototype,
  }
}
