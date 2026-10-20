/** 任务发布 — SOP 参数表单状态 + 提交前校验 + 提交（multipart） */
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { listAgents } from "../api/agents"
import { listDevices, submitTask } from "../api/tasks"
import { taskDeviceAddress } from "../helpers/task-device-address"
import { parseCaseTitles } from "../helpers/yaml-case-titles"
import { TASK_DEVICE_POLL_INTERVAL_MS } from "../constants"
import type { AgentRecord } from "@/shared/types/ai"
import type { DeviceRecord } from "@/shared/types/device"

export interface TaskFormState {
  title: string
  /** 选中的智能体 id；null = 未选择（提交置灰） */
  agent_id: number | null
  /** 唯一配置：YAML */
  configFile: File | null
  device_serial: string
  /** 指定用例标题；空串 = 全部用例 */
  case_title: string
}

export interface AgentOption {
  id: number
  label: string
}

const CONFIG_ACCEPT = ".yaml,.yml"

function emptyForm(): TaskFormState {
  return {
    title: "",
    agent_id: null,
    configFile: null,
    device_serial: "",
    case_title: "",
  }
}

function deviceLabelOf(d: DeviceRecord): string {
  return (d.model || d.name || "").trim()
}

export function useTaskPublish() {
  const form = ref<TaskFormState>(emptyForm())
  const submitting = ref(false)
  const devices = ref<DeviceRecord[]>([])
  const agents = ref<AgentRecord[]>([])
  const caseTitles = ref<string[]>([])
  const caseError = ref("")
  const dialogVisible = ref(false)

  const agentOptions = computed<AgentOption[]>(() =>
    agents.value.map((agent) => ({
      id: agent.id,
      label: (agent.route_configs?.device_control?.name || agent.name || "未命名智能体").trim(),
    })),
  )

  async function loadAgents() {
    try {
      const data = await listAgents()
      agents.value = data.status && data.data ? data.data.agents || [] : []
    } catch {
      agents.value = []
    }
  }

  let devicePollTimer: ReturnType<typeof setInterval> | null = null

  function openDialog() {
    dialogVisible.value = true
  }
  function closeDialog() {
    dialogVisible.value = false
  }

  async function loadDevices() {
    try {
      const data = await listDevices()
      if (data.status && data.data) {
        devices.value = data.data.devices || []
      }
    } catch {
      // 设备列表加载失败不阻断提交：下拉为空时由必填校验拦住
    }
  }

  function stopDevicePoll() {
    if (devicePollTimer) {
      clearInterval(devicePollTimer)
      devicePollTimer = null
    }
  }

  function startDevicePoll() {
    stopDevicePoll()
    void loadDevices()
    devicePollTimer = setInterval(() => {
      void loadDevices()
    }, TASK_DEVICE_POLL_INTERVAL_MS)
  }

  watch(dialogVisible, (open) => {
    if (open) {
      startDevicePoll()
      void loadAgents()
    } else stopDevicePoll()
  })

  onUnmounted(stopDevicePoll)

  function canSubmit(): boolean {
    return (
      form.value.title.trim() !== "" &&
      form.value.agent_id !== null &&
      form.value.configFile !== null &&
      form.value.device_serial.trim() !== ""
    )
  }

  /** 选 YAML：解析标题；换文件时清空已选用例。 */
  async function onConfigChange(file: File | null) {
    form.value.configFile = file
    form.value.case_title = ""
    caseTitles.value = []
    caseError.value = ""
    if (!file) return
    try {
      const parsed = parseCaseTitles(await file.text())
      caseTitles.value = parsed.titles
      caseError.value = parsed.error
    } catch {
      caseError.value = "读取 YAML 失败，请重新选择文件"
    }
  }

  function clearConfig() {
    form.value.configFile = null
    form.value.case_title = ""
    caseTitles.value = []
    caseError.value = ""
  }

  async function submit(onSuccess?: () => void) {
    if (!canSubmit()) {
      ElMessage.warning("请填写任务标题、选择智能体、YAML 与设备")
      return
    }
    submitting.value = true
    try {
      const fd = new FormData()
      fd.append("title", form.value.title.trim())
      fd.append("agent_id", String(form.value.agent_id))
      fd.append("device_serial", form.value.device_serial.trim())
      fd.append("case_title", form.value.case_title.trim())
      const hit = devices.value.find((d) => taskDeviceAddress(d) === form.value.device_serial)
      const label = hit ? deviceLabelOf(hit) : ""
      if (label) fd.append("device_label", label)
      if (form.value.configFile) {
        fd.append("config", form.value.configFile)
      }
      const data = await submitTask(fd)
      if (data.status) {
        ElMessage.success("任务已提交")
        form.value = emptyForm()
        clearConfig()
        onSuccess?.()
      } else {
        ElMessage.error(data.message || "提交失败")
      }
    } catch (err: unknown) {
      ElMessage.error(formatApiError(err as never, "提交失败，请稍后重试"))
    }
    submitting.value = false
  }

  onMounted(() => {
    void loadDevices()
    void loadAgents()
  })

  return {
    form,
    submitting,
    devices,
    agents,
    agentOptions,
    caseTitles,
    caseError,
    dialogVisible,
    CONFIG_ACCEPT,
    openDialog,
    closeDialog,
    canSubmit,
    submit,
    loadDevices,
    onConfigChange,
    clearConfig,
  }
}
