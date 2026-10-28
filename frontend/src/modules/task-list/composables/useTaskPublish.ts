/** 任务发布 — SOP 参数表单状态 + 提交前校验 + 提交（multipart） */
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { ElMessage } from "element-plus"
import type { UploadFile } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { listAgents } from "@/modules/ai-assistant/api/agents"
import { TASK_KIND_CASE_AUTHORING } from "@/modules/ai-assistant/constants"
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
  /** 设备执行：唯一配置 YAML */
  configFile: File | null
  device_serial: string
  /** 指定用例标题；空串 = 全部用例 */
  case_title: string
  /** 用例编写：PRD / Word 文档 */
  documents: File[]
}

export interface AgentOption {
  id: number
  label: string
  taskKind: string
}

const CONFIG_ACCEPT = ".yaml,.yml"
const DOCUMENT_ACCEPT = ".docx,.pdf,.md"

function emptyForm(): TaskFormState {
  return {
    title: "",
    agent_id: null,
    configFile: null,
    device_serial: "",
    case_title: "",
    documents: [],
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
      label: (
        agent.route_configs?.device_control?.name ||
        agent.route_configs?.case_authoring?.name ||
        agent.name ||
        "未命名智能体"
      ).trim(),
      taskKind: agent.task_kind || "device_control",
    })),
  )

  /** 当前选中的 Agent 是否为用例编写类型 */
  const isCaseAuthoring = computed(() => {
    const picked = agents.value.find((agent) => agent.id === form.value.agent_id)
    return picked?.task_kind === TASK_KIND_CASE_AUTHORING
  })

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

  // 切换智能体时只清掉与目标任务类型不兼容的字段：
  // 选 Agent-02 清设备/YAML/指定用例；选设备执行 Agent 清 PRD/Word 文档。
  watch(
    () => form.value.agent_id,
    () => {
      const picked = agents.value.find((agent) => agent.id === form.value.agent_id)
      if (picked?.task_kind === TASK_KIND_CASE_AUTHORING) {
        form.value.configFile = null
        form.value.case_title = ""
        caseTitles.value = []
        caseError.value = ""
        form.value.device_serial = ""
      } else {
        form.value.documents = []
      }
    },
    { flush: "sync" },
  )

  onUnmounted(stopDevicePoll)

  function canSubmit(): boolean {
    if (form.value.title.trim() === "" || form.value.agent_id === null) return false
    if (isCaseAuthoring.value) return form.value.documents.length > 0
    return form.value.configFile !== null && form.value.device_serial.trim() !== ""
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

  /** 用例编写：收下一份 PRD / Word 文档。 */
  function onDocumentChange(file: UploadFile) {
    const raw = file.raw
    if (!raw) return
    if (!/\.(docx|pdf|md)$/i.test(raw.name || "")) {
      ElMessage.error("仅支持 .docx / .pdf / .md 文档")
      return
    }
    if (raw.size > 20 * 1024 * 1024) {
      ElMessage.error("文件过大（上限 20MB）")
      return
    }
    form.value.documents = [
      ...form.value.documents.filter((item) => item.name !== raw.name || item.size !== raw.size),
      raw,
    ]
  }

  /** 用例编写：移除一份文档。 */
  function onDocumentRemove(file: UploadFile) {
    const raw = file.raw
    if (!raw) return
    form.value.documents = form.value.documents.filter(
      (item) => item.name !== raw.name || item.size !== raw.size,
    )
  }

  function clearDocuments() {
    form.value.documents = []
  }

  async function submit(onSuccess?: () => void) {
    if (!canSubmit()) {
      ElMessage.warning(
        isCaseAuthoring.value
          ? "请填写任务标题、选择 Agent-02 并上传 PRD / Word 文档"
          : "请填写任务标题、选择智能体、YAML 与设备",
      )
      return
    }
    submitting.value = true
    try {
      const fd = new FormData()
      fd.append("title", form.value.title.trim())
      fd.append("agent_id", String(form.value.agent_id))
      if (isCaseAuthoring.value) {
        for (const doc of form.value.documents) {
          fd.append("documents", doc)
        }
      } else {
        fd.append("device_serial", form.value.device_serial.trim())
        fd.append("case_title", form.value.case_title.trim())
        const hit = devices.value.find((d) => taskDeviceAddress(d) === form.value.device_serial)
        const label = hit ? deviceLabelOf(hit) : ""
        if (label) fd.append("device_label", label)
        if (form.value.configFile) {
          fd.append("config", form.value.configFile)
        }
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
    isCaseAuthoring,
    caseTitles,
    caseError,
    dialogVisible,
    CONFIG_ACCEPT,
    DOCUMENT_ACCEPT,
    openDialog,
    closeDialog,
    canSubmit,
    submit,
    loadDevices,
    onConfigChange,
    clearConfig,
    onDocumentChange,
    onDocumentRemove,
    clearDocuments,
  }
}
