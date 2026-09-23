/** useModelDebug — 单模型调试台（角色只读配置 + 设备候选 + 单角色对话；挂真实工具、不落库） */
import { computed, ref, watch } from "vue"
import type { Ref } from "vue"
import { ElMessage } from "element-plus"
import {
  fetchModelDebugConfig,
  chatWithModelDebug,
  type ModelDebugConfig,
  type ModelDebugRole,
  type ModelDebugRoleConfig,
  type ModelDebugToolCall,
} from "../api/toolbox"
import { listDevices } from "../api/tasks"
import { MODEL_DEBUG_DEVICE_REQUIRED_HINT } from "../constants"
import { formatApiError } from "@/shared/api-client"
import type { DeviceRecord } from "@/shared/types/device"

export const MODEL_DEBUG_ROLES: ModelDebugRole[] = ["planner", "executor", "verifier"]

export interface ModelDebugMessage {
  id: number
  role: "user" | "assistant"
  content: string
  model_name?: string
  thinking?: string[]
  tool_usage?: ModelDebugToolCall[]
  cost?: number
  error?: boolean
}

/** 单角色调试页：加载配置 + 设备候选 + 发送对话（消息仅存内存，对话不落库） */
export function useModelDebug(role: Ref<string>) {
  const config = ref<ModelDebugConfig | null>(null)
  const loading = ref(false)
  const error = ref("")
  const question = ref("")
  const sending = ref(false)
  const messages = ref<ModelDebugMessage[]>([])
  /** 调试设备候选：对请求者可见 + 状态在线 + 未被占用（与平台工具调试页同口径） */
  const devices = ref<DeviceRecord[]>([])
  const devicesLoading = ref(false)
  const serial = ref("")
  let seq = 0

  const needsDevice = computed(() => config.value?.role.needs_device === true)
  const canSend = computed(
    () =>
      Boolean(question.value.trim()) &&
      !sending.value &&
      (!needsDevice.value || Boolean(serial.value)),
  )

  async function load(): Promise<void> {
    loading.value = true
    error.value = ""
    try {
      const data = await fetchModelDebugConfig(role.value)
      if (data.status && data.data) config.value = data.data
      else error.value = data.message || "调试配置加载失败"
    } catch (e) {
      error.value = formatApiError(e, "调试配置加载失败")
    }
    loading.value = false
  }

  async function loadDevices(): Promise<void> {
    devicesLoading.value = true
    try {
      const data = await listDevices()
      const rows = data.status && data.data ? data.data.devices || [] : []
      devices.value = rows.filter((item) => item.status === "ONLINE" && !item.occupied_by)
    } catch (e) {
      devices.value = []
      ElMessage.error(formatApiError(e, "调试设备候选加载失败"))
    }
    devicesLoading.value = false
  }

  async function send(): Promise<void> {
    const text = question.value.trim()
    if (!text || sending.value) return
    // 需要设备的角色没选设备就不发：后端也会拦，这里先给出可读提示
    if (needsDevice.value && !serial.value) {
      ElMessage.warning(MODEL_DEBUG_DEVICE_REQUIRED_HINT)
      return
    }
    messages.value.push({ id: ++seq, role: "user", content: text })
    question.value = ""
    sending.value = true
    try {
      const data = await chatWithModelDebug(role.value, text, serial.value)
      if (data.status && data.data) {
        messages.value.push({
          id: ++seq,
          role: "assistant",
          content: data.data.reply || "（空回复）",
          model_name: data.data.model_name,
          thinking: data.data.thinking || [],
          tool_usage: data.data.tool_usage || [],
          cost: data.data.cost,
        })
      } else {
        messages.value.push({
          id: ++seq,
          role: "assistant",
          content: data.message || "调用失败",
          error: true,
        })
      }
    } catch (e) {
      messages.value.push({
        id: ++seq,
        role: "assistant",
        content: formatApiError(e, "调试对话失败"),
        error: true,
      })
    }
    sending.value = false
  }

  function clearMessages(): void {
    messages.value = []
  }

  watch(
    role,
    () => {
      config.value = null
      messages.value = []
      void load()
      void loadDevices()
    },
    { immediate: true },
  )

  return {
    config,
    loading,
    error,
    question,
    sending,
    messages,
    devices,
    devicesLoading,
    serial,
    needsDevice,
    canSend,
    load,
    loadDevices,
    send,
    clearMessages,
  }
}

/** 工具箱「模型调试」来源：三个角色卡片的概览（三角色各拉一次只读配置） */
export function useModelDebugRoles() {
  const roles = ref<ModelDebugRoleConfig[]>([])
  const loading = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    try {
      const results = await Promise.all(
        MODEL_DEBUG_ROLES.map((role) => fetchModelDebugConfig(role)),
      )
      roles.value = results
        .map((res) => (res.status && res.data ? res.data.role : null))
        .filter((item): item is ModelDebugRoleConfig => Boolean(item))
    } catch (e) {
      ElMessage.error(formatApiError(e, "模型调试配置加载失败"))
    }
    loading.value = false
  }

  return { roles, loading, load }
}
