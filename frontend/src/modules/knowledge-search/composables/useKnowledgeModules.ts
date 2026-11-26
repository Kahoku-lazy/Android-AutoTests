import { ref } from "vue"
import { formatApiError } from "@/shared/api-client"
import {
  createKnowledgeModule,
  deleteKnowledgeModule,
  fetchKnowledgeModules,
  indexKnowledgeModule,
  updateKnowledgeModule,
} from "../api"
import type { IndexOutcome, KnowledgeModuleRow, ModulePayload } from "../types"

export function useKnowledgeModules() {
  const modules = ref<KnowledgeModuleRow[]>([])
  const loading = ref(false)
  const error = ref("")

  const selected = ref<string[]>([])

  async function load(): Promise<void> {
    loading.value = true
    error.value = ""
    try {
      const response = await fetchKnowledgeModules()
      if (response.status) {
        modules.value = response.data?.modules ?? []

        const alive = new Set(modules.value.filter((m) => m.enabled).map((m) => m.name))
        selected.value = selected.value.filter((name) => alive.has(name))
      } else {
        error.value = response.message || "模块列表加载失败"
      }
    } catch (exc) {
      error.value = formatApiError(exc)
    } finally {
      loading.value = false
    }
  }

  function toggleSelect(name: string): void {
    selected.value = selected.value.includes(name)
      ? selected.value.filter((item) => item !== name)
      : [...selected.value, name]
  }

  async function save(
    payload: ModulePayload,
    id?: number,
  ): Promise<{ ok: boolean; message: string }> {
    try {
      const response = id
        ? await updateKnowledgeModule(id, payload)
        : await createKnowledgeModule(payload)
      if (!response.status) return { ok: false, message: response.message || "保存失败" }
      await load()
      return { ok: true, message: "" }
    } catch (exc) {
      return { ok: false, message: formatApiError(exc) }
    }
  }

  async function remove(id: number): Promise<{ ok: boolean; message: string }> {
    try {
      const response = await deleteKnowledgeModule(id)
      if (!response.status) return { ok: false, message: response.message || "删除失败" }
      await load()
      return { ok: true, message: "" }
    } catch (exc) {
      return { ok: false, message: formatApiError(exc) }
    }
  }

  async function toggleEnabled(row: KnowledgeModuleRow): Promise<{ ok: boolean; message: string }> {
    return save(
      {
        name: row.name,
        description: row.description,
        data_dir: row.data_dir,
        enabled: !row.enabled,
      },
      row.id,
    )
  }

  async function rebuildIndex(
    id: number,
  ): Promise<{ ok: boolean; outcome?: IndexOutcome; message: string }> {
    try {
      const response = await indexKnowledgeModule(id)
      if (!response.status || !response.data) {
        return { ok: false, message: response.message || "索引失败" }
      }
      return { ok: response.data.ok, outcome: response.data, message: response.data.error }
    } catch (exc) {
      return { ok: false, message: formatApiError(exc) }
    }
  }

  return {
    modules,
    loading,
    error,
    selected,
    load,
    toggleSelect,
    save,
    remove,
    toggleEnabled,
    rebuildIndex,
  }
}
