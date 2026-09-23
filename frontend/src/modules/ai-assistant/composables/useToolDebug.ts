/** useToolDebug — 平台工具调试页：拉 schema、填表单、确认后 invoke。 */
import { computed, ref, watch, type Ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import {
  fetchPlatformToolSchema,
  invokePlatformTool,
  type PlatformToolDebugSchema,
} from "../api/toolbox"

export type ToolDebugFormValues = Record<string, string | number | boolean>

function defaultFormValues(schema: PlatformToolDebugSchema | null): ToolDebugFormValues {
  const values: ToolDebugFormValues = {}
  if (!schema) return values
  for (const p of schema.parameters) {
    if (p.default !== undefined) {
      values[p.name] = p.default as string | number | boolean
    } else if (p.type === "bool") {
      values[p.name] = false
    } else if (p.type === "int" || p.type === "float") {
      values[p.name] = 0
    } else {
      values[p.name] = ""
    }
  }
  return values
}

function buildParams(
  schema: PlatformToolDebugSchema,
  form: ToolDebugFormValues,
): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const p of schema.parameters) {
    if (p.name === "user_id") continue
    const raw = form[p.name]
    if (raw === "" || raw === undefined || raw === null) {
      if (p.required) {
        throw new Error(`请填写必填参数：${p.name}`)
      }
      continue
    }
    if (p.type === "int") {
      out[p.name] = Number.parseInt(String(raw), 10)
    } else if (p.type === "float") {
      out[p.name] = Number.parseFloat(String(raw))
    } else if (p.type === "bool") {
      out[p.name] = Boolean(raw)
    } else {
      out[p.name] = String(raw)
    }
  }
  return out
}

export interface ScreenshotPreview {
  mediaType: string
  dataUrl: string
  summary: unknown
}

export function extractScreenshotPreview(result: unknown): ScreenshotPreview | null {
  if (!result || typeof result !== "object") return null
  const obj = result as { image?: { base64?: string; media_type?: string }; summary?: unknown }
  const b64 = obj.image?.base64
  if (!b64) return null
  const mediaType = obj.image?.media_type || "image/jpeg"
  return {
    mediaType,
    dataUrl: `data:${mediaType};base64,${b64}`,
    summary: obj.summary ?? null,
  }
}

export function displayResultJson(result: unknown): string {
  const shot = extractScreenshotPreview(result)
  if (shot) {
    return JSON.stringify({ summary: shot.summary }, null, 2)
  }
  return JSON.stringify(result, null, 2)
}

export function useToolDebug(toolName: Ref<string>, canExecuteWrite: Ref<boolean>) {
  const schema = ref<PlatformToolDebugSchema | null>(null)
  const form = ref<ToolDebugFormValues>({})
  const loading = ref(false)
  const invoking = ref(false)
  const error = ref("")
  const invokeError = ref("")
  const result = ref<unknown>(null)

  const canExecute = computed(() => {
    if (!schema.value) return false
    if (schema.value.read_only) return true
    return canExecuteWrite.value
  })

  const screenshot = computed(() => extractScreenshotPreview(result.value))
  const resultText = computed(() => (result.value == null ? "" : displayResultJson(result.value)))

  async function loadSchema() {
    const name = toolName.value
    if (!name) {
      schema.value = null
      form.value = {}
      error.value = "缺少工具名"
      return
    }
    loading.value = true
    error.value = ""
    result.value = null
    invokeError.value = ""
    try {
      const data = await fetchPlatformToolSchema(name)
      if (!data.status || !data.data) {
        schema.value = null
        form.value = {}
        error.value = data.message || "加载工具 schema 失败"
        return
      }
      schema.value = data.data
      form.value = defaultFormValues(data.data)
    } catch (e) {
      schema.value = null
      form.value = {}
      error.value = formatApiError(e as never, "加载工具 schema 失败")
    } finally {
      loading.value = false
    }
  }

  async function runInvoke() {
    if (!schema.value) return
    if (!canExecute.value) {
      ElMessage.warning("写工具仅超级管理员可执行")
      return
    }
    let params: Record<string, unknown>
    try {
      params = buildParams(schema.value, form.value)
    } catch (e) {
      ElMessage.error(e instanceof Error ? e.message : "参数无效")
      return
    }

    if (!schema.value.read_only) {
      try {
        await ElMessageBox.confirm(
          `「${schema.value.name}」是写操作，将产生真实副作用（如锁定设备、点击屏幕）。确定执行？`,
          "确认执行写工具",
          { type: "warning", confirmButtonText: "执行", cancelButtonText: "取消" },
        )
      } catch {
        return
      }
    }

    invoking.value = true
    invokeError.value = ""
    result.value = null
    try {
      const data = await invokePlatformTool(schema.value.name, params)
      if (!data.status) {
        invokeError.value = data.message || "执行失败"
        ElMessage.error(invokeError.value)
        return
      }
      result.value = data.data?.result ?? null
    } catch (e) {
      invokeError.value = formatApiError(e as never, "执行失败")
      ElMessage.error(invokeError.value)
    } finally {
      invoking.value = false
    }
  }

  watch(
    toolName,
    () => {
      void loadSchema()
    },
    { immediate: true },
  )

  return {
    schema,
    form,
    loading,
    invoking,
    error,
    invokeError,
    result,
    resultText,
    screenshot,
    canExecute,
    loadSchema,
    runInvoke,
  }
}
