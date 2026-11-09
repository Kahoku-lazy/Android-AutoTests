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
import { usePlatformCases } from "./usePlatformCases"
import {
  CASE_SOURCE_DEFAULT,
  CASE_SOURCE_PLATFORM,
  TASK_DEVICE_POLL_INTERVAL_MS,
  type CaseSource,
} from "../constants"
import type { AgentRecord } from "@/shared/types/ai"
import type { DeviceRecord } from "@/shared/types/device"

export interface TaskFormState {
  title: string
  /** 选中的智能体 id；null = 未选择（提交置灰） */
  agent_id: number | null
  /** 设备执行：用例来源（平台用例 / 本地 YAML） */
  case_source: CaseSource
  /** 设备执行：唯一配置 YAML（本地 YAML 来源） */
  configFile: File | null
  /** 设备执行：平台用例编号（平台用例来源） */
  caseIds: string[]
  device_serial: string
  /** 指定用例标题；空串 = 全部用例（仅本地 YAML 来源） */
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
    case_source: CASE_SOURCE_DEFAULT,
    configFile: null,
    caseIds: [],
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
  /** 平台用例选择器：项目 → 用例表 → 用例 */
  const platform = usePlatformCases()

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
      void platform.loadProjects()
    } else stopDevicePoll()
  })

  // 切换智能体时只清掉与目标任务类型不兼容的字段：
  // 选 Agent-02 清设备/用例来源/指定用例；选设备执行 Agent 清 PRD/Word 文档。
  watch(
    () => form.value.agent_id,
    () => {
      const picked = agents.value.find((agent) => agent.id === form.value.agent_id)
      if (picked?.task_kind === TASK_KIND_CASE_AUTHORING) {
        clearConfig()
        form.value.caseIds = []
        platform.reset()
        form.value.device_serial = ""
      } else {
        form.value.documents = []
      }
    },
    { flush: "sync" },
  )

  // 切换用例来源时清掉另一侧的已选内容：平台用例与本地 YAML 不混用
  watch(
    () => form.value.case_source,
    (source) => {
      if (source === CASE_SOURCE_PLATFORM) {
        clearConfig()
        return
      }
      form.value.caseIds = []
    },
  )

  onUnmounted(stopDevicePoll)

  function canSubmit(): boolean {
    if (form.value.title.trim() === "" || form.value.agent_id === null) return false
    if (isCaseAuthoring.value) return form.value.documents.length > 0
    if (form.value.device_serial.trim() === "") return false
    if (form.value.case_source === CASE_SOURCE_PLATFORM) return form.value.caseIds.length > 0
    return form.value.configFile !== null
  }

  /** 平台用例：切项目 / 切表都清空已选用例，避免跨表编号混在一起 */
  async function onPlatformProjectChange(projectId: number | null) {
    form.value.caseIds = []
    await platform.loadFiles(projectId)
  }

  async function onPlatformFileChange(fileId: number | null) {
    form.value.caseIds = []
    await platform.loadCases(fileId)
  }

  function onPlatformCasesChange(caseIds: string[]) {
    form.value.caseIds = caseIds
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
      if (isCaseAuthoring.value) {
        ElMessage.warning("请填写任务标题、选择 Agent-02 并上传 PRD / Word 文档")
      } else if (form.value.case_source === CASE_SOURCE_PLATFORM) {
        ElMessage.warning("请填写任务标题、选择智能体、设备与至少一条平台用例")
      } else {
        ElMessage.warning("请填写任务标题、选择智能体、YAML 与设备")
      }
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
        fd.append("case_source", form.value.case_source)
        const hit = devices.value.find((d) => taskDeviceAddress(d) === form.value.device_serial)
        const label = hit ? deviceLabelOf(hit) : ""
        if (label) fd.append("device_label", label)
        if (form.value.case_source === CASE_SOURCE_PLATFORM) {
          fd.append("case_ids", JSON.stringify(form.value.caseIds))
        } else {
          fd.append("case_title", form.value.case_title.trim())
          if (form.value.configFile) {
            fd.append("config", form.value.configFile)
          }
        }
      }
      const data = await submitTask(fd)
      if (data.status) {
        ElMessage.success("任务已提交")
        form.value = emptyForm()
        clearConfig()
        platform.reset()
        onSuccess?.()
      } else {
        ElMessage.error(data.message || "提交失败")
      }
    } catch (err: unknown) {
      ElMessage.error(formatApiError(err as never, "提交失败，请稍后重试"))
    }
    submitting.value = false
  }

  // 智能体列表在挂载时加载（响应已瘦身到 KB 级）；设备列表要同步 ADB，
  // 只在打开「新建任务」弹窗时按需加载（watch dialogVisible）。
  onMounted(() => {
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
    platform,
    CONFIG_ACCEPT,
    DOCUMENT_ACCEPT,
    openDialog,
    closeDialog,
    canSubmit,
    submit,
    loadDevices,
    onConfigChange,
    clearConfig,
    onPlatformProjectChange,
    onPlatformFileChange,
    onPlatformCasesChange,
    onDocumentChange,
    onDocumentRemove,
    clearDocuments,
  }
}
