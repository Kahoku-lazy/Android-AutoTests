/** 平台小助手入口：左侧竖排编排，右侧对话面板；可切换查看模型事件。 */
import { computed, onMounted, ref, watch } from "vue"
import { apiListDevices } from "@/modules/device-pool/api"
import {
  fetchWorkflowEvents,
  listWorkflows,
  sendWorkflowMessage,
  type WorkflowCard,
} from "./api/workflows"

export type BoardView = "chat" | "events"

export function useSingleAgentBoard() {
  const workflows = ref<WorkflowCard[]>([])
  const selectedKey = ref("")
  const serial = ref("")
  const devices = ref<{ serial: string; model: string }[]>([])
  const draft = ref("")
  const loading = ref(false)
  const sending = ref(false)
  const errorText = ref("")
  const view = ref<BoardView>("chat")
  const events = ref<string[]>([])
  const eventsLoading = ref(false)

  // 每张编排一条独立会话与一份回复，切换后互不串台。
  const replies = ref<Record<string, string>>({})
  const sessionIds = ref<Record<string, string>>({})

  const selected = computed(() => workflows.value.find((item) => item.key === selectedKey.value) ?? null)
  const currentReply = computed(() => (selectedKey.value ? replies.value[selectedKey.value] ?? "" : ""))
  const currentSession = computed(() => (selectedKey.value ? sessionIds.value[selectedKey.value] ?? "" : ""))
  const canSend = computed(() => Boolean(selected.value && serial.value && draft.value.trim() && !sending.value))
  const sendHint = computed(() => (serial.value ? "" : "先选择设备"))

  function sessionOf(key: string): string {
    const existing = sessionIds.value[key]
    if (existing) return existing
    const created = crypto.randomUUID()
    sessionIds.value = { ...sessionIds.value, [key]: created }
    return created
  }

  async function load() {
    loading.value = true
    errorText.value = ""
    try {
      const [cards, devicePage] = await Promise.all([listWorkflows(), apiListDevices()])
      workflows.value = cards
      const records = devicePage.data.data?.devices ?? []
      devices.value = records.map((item) => ({
        serial: item.serial,
        model: item.model || item.name || item.serial,
      }))
      selectedKey.value = cards[0]?.key ?? ""
    } catch {
      errorText.value = "编排清单加载失败"
    } finally {
      loading.value = false
    }
  }

  async function loadEvents() {
    const session = currentSession.value
    if (!session) {
      events.value = []
      return
    }
    eventsLoading.value = true
    try {
      events.value = await fetchWorkflowEvents(session)
    } catch {
      errorText.value = "事件读取失败"
    } finally {
      eventsLoading.value = false
    }
  }

  async function send() {
    if (!canSend.value || !selected.value) return
    const key = selected.value.key
    sending.value = true
    errorText.value = ""
    try {
      replies.value = {
        ...replies.value,
        [key]: await sendWorkflowMessage({
          key,
          serial: serial.value,
          message: draft.value.trim(),
          sessionId: sessionOf(key),
        }),
      }
      draft.value = ""
      if (view.value === "events") await loadEvents()
    } catch {
      errorText.value = "发送失败，请重试"
    } finally {
      sending.value = false
    }
  }

  async function toggleView() {
    view.value = view.value === "events" ? "chat" : "events"
    if (view.value === "events") await loadEvents()
  }

  // 切换编排：清草稿与错误，回复各自保留。
  watch(selectedKey, () => {
    draft.value = ""
    errorText.value = ""
    events.value = []
  })

  onMounted(load)
  return {
    workflows,
    selectedKey,
    serial,
    devices,
    draft,
    view,
    events,
    eventsLoading,
    currentReply,
    loading,
    sending,
    errorText,
    canSend,
    sendHint,
    load,
    loadEvents,
    send,
    toggleView,
  }
}
