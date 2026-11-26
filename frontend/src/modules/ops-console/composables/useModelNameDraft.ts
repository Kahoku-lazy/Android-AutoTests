import { computed, ref, watch, type Ref } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { discoverModelNames } from "../api"
import type { OpsModelConfigInput } from "../types"

export interface NameRow {
  key: number
  value: string
}

export function useModelNameDraft(form: Ref<OpsModelConfigInput>) {
  const rows = ref<NameRow[]>([])
  const loading = ref(false)
  const hint = ref("")

  let seq = 0

  function makeRow(value: string): NameRow {
    seq += 1
    return { key: seq, value }
  }

  function reset(names: string[]): void {
    rows.value = (names.length ? names : [""]).map(makeRow)
  }

  function add(): void {
    rows.value.push(makeRow(""))
  }

  function remove(index: number): void {
    if (index < 0 || index >= rows.value.length) return
    rows.value.splice(index, 1)
  }

  const single = computed({
    get: () => rows.value[0]?.value ?? "",
    set: (value: string) => {
      if (rows.value.length) rows.value[0].value = value
      else rows.value = [makeRow(value)]
    },
  })

  function names(): string[] {
    const picked = form.value.model_kind === "chat" ? rows.value : rows.value.slice(0, 1)
    const seen: string[] = []
    for (const row of picked) {
      const name = row.value.trim()
      if (name && !seen.includes(name)) seen.push(name)
    }
    return seen
  }

  function validUrl(value: string, kind = form.value.model_kind): boolean {
    const allowed = kind === "realtime" ? ["http:", "https:", "ws:", "wss:"] : ["http:", "https:"]
    try {
      return allowed.includes(new URL(value.trim()).protocol)
    } catch {
      return false
    }
  }

  async function discover(): Promise<void> {
    if (!validUrl(form.value.base_url)) {
      const message = form.value.base_url.trim()
        ? "API 地址必须是 http 或 https 链接"
        : "API 地址不能为空"
      hint.value = message
      ElMessage.error(message)
      return
    }
    loading.value = true
    hint.value = ""
    try {
      const { data } = await discoverModelNames(form.value)
      if (!data.status || !data.data) throw data
      const found = data.data.models || []
      if (found.length) {
        reset(found)
        hint.value = `已加载 ${found.length} 个模型，可逐行删掉不需要的`
        ElMessage.success(hint.value)
        return
      }
      hint.value = data.data.reason || "模型列表为空"
      ElMessage.warning(hint.value)
    } catch (e) {
      hint.value = formatApiError(e as never, "模型加载失败")
      ElMessage.error(hint.value)
    } finally {
      loading.value = false
    }
  }

  watch(
    () => form.value.model_kind,
    (kind) => {
      if (kind !== "chat" && rows.value.length > 1) rows.value = rows.value.slice(0, 1)
    },
  )

  return { rows, loading, hint, single, reset, add, remove, names, validUrl, discover }
}
