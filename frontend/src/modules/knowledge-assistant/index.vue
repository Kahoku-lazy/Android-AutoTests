<script setup lang="ts">
/**
 * 知识库助手页面：语音按键 + 实时对话记录 + 本地日志落点。
 *
 * 页面只做三态取数与事件编排；音频、WS 与消息归并分别在 audio/、
 * composables/ 与 helpers/ 中。
 */
import {
  computed,
  nextTick,
  onActivated,
  onBeforeUnmount,
  onDeactivated,
  onMounted,
  ref,
  watch,
} from "vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { getApiErrorMessage } from "@/shared/types/api-error"
import VoiceConsole from "./components/VoiceConsole.vue"
import TranscriptPanel from "./components/TranscriptPanel.vue"
import { useVoiceSession } from "./composables/useVoiceSession"
import { fetchKnowledgeAssistantStatus } from "./api"
import {
  KB_ICON_GRADIENT,
  KB_MODE_LIVETRANSLATE,
  KB_MODE_OMNI,
  KB_MODE_PIPELINE,
  KB_PAGE_ICON,
  KB_PAGE_SUBTITLE,
  KB_PAGE_SUBTITLE_PIPELINE,
  KB_PAGE_TITLE,
  KB_ROUTE_OPTIONS,
  type KbRoute,
  KB_READY_FALLBACK,
  KB_STATUS_LOAD_ERROR,
  KB_STATUS_TEXT,
} from "./constants"
import type { KnowledgeAssistantStatus } from "./types"

const status = ref<KnowledgeAssistantStatus | null>(null)
const statusError = ref("")
const loading = ref(true)
const bottomRef = ref<HTMLElement | null>(null)
const selectedRoute = ref<KbRoute>("omni")

const {
  messages,
  state,
  errorMessage,
  noticeMessage,
  session,
  micLevel,
  sentFrames,
  devices,
  selectedDeviceId,
  loadDevices,
  canInterrupt,
  start,
  sendText,
  stop,
  interrupt,
  dispose,
} = useVoiceSession()

const canStart = computed(() => status.value?.ready === true)
const showTextInput = computed(() => selectedRoute.value === "pipeline")
const statusText = computed(() => KB_STATUS_TEXT[state.value])
const pageSubtitle = computed(() =>
  selectedRoute.value === "pipeline" ? KB_PAGE_SUBTITLE_PIPELINE : KB_PAGE_SUBTITLE,
)
const modeLabel = computed(() => {
  const mode = session.value?.mode || selectedRoute.value
  if (mode === "pipeline") return KB_MODE_PIPELINE
  if (mode === "livetranslate") return KB_MODE_LIVETRANSLATE
  return KB_MODE_OMNI
})
const modelLabel = computed(() => {
  if (session.value) return `${session.value.model} · ${session.value.voice}`
  if (selectedRoute.value === "pipeline") {
    const llm = status.value?.pipeline_llm_model || "deepseek-flash"
    const tts = status.value?.pipeline_tts_model || "sambert-zhichu-v1"
    const voice = status.value?.pipeline_tts_voice || "知厨"
    return `${llm} + ${tts} · ${voice}`
  }
  if (status.value) return `${status.value.model} · ${status.value.voice}`
  return "—"
})
const logPath = computed(
  () => session.value?.logPath || status.value?.log_file || status.value?.log_dir || "—",
)
const unavailableReason = computed(() => status.value?.reason || KB_READY_FALLBACK)

async function loadStatus(): Promise<void> {
  loading.value = true
  statusError.value = ""
  try {
    status.value = await fetchKnowledgeAssistantStatus()
  } catch (error) {
    statusError.value = getApiErrorMessage(error, KB_STATUS_LOAD_ERROR)
  } finally {
    loading.value = false
  }
}

function onStart(): void {
  if (!canStart.value) return
  void start(selectedRoute.value)
}

function onDeviceChange(deviceId: string): void {
  selectedDeviceId.value = deviceId
}

function onRouteChange(route: KbRoute): void {
  selectedRoute.value = route
}

function onTextSubmit(text: string): void {
  if (!canStart.value) return
  void sendText(text, selectedRoute.value)
}

watch(
  status,
  (value) => {
    if (value?.mode === "pipeline") selectedRoute.value = "pipeline"
    else if (value?.mode === "omni") selectedRoute.value = "omni"
  },
  { immediate: true },
)

onMounted(loadStatus)
onMounted(loadDevices)
// 工作台用 keep-alive：离开页面是 deactivate 而不是 unmount，必须在这里释放麦克风与 WS
onDeactivated(dispose)
onBeforeUnmount(dispose)
onActivated(() => {
  if (!status.value && !loading.value) void loadStatus()
})

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    bottomRef.value?.scrollIntoView({ behavior: "smooth", block: "end" })
  },
)
</script>

<template>
  <div
    class="doc-page doc-page--fixed wb-shell kb-workbench"
    data-testid="knowledge-assistant-page"
  >
    <WorkbenchHeader
      :title="KB_PAGE_TITLE"
      :subtitle="pageSubtitle"
      :icon="KB_PAGE_ICON"
      :icon-gradient="KB_ICON_GRADIENT"
    />

    <div class="doc-body kb-body">
      <SkeletonCard v-if="loading" variant="list" :lines="6" />

      <ErrorState v-else-if="statusError" :message="statusError" @retry="loadStatus" />

      <template v-else>
        <ErrorState v-if="!canStart" :message="unavailableReason" @retry="loadStatus" />
        <p v-if="!canStart" class="kb-notice-hint">
          按上面的原因处理后点击「重试」，就绪后语音按键才可用。
        </p>

        <div class="kb-layout">
          <div class="kb-console-wrap">
            <VoiceConsole
              :state="state"
              :status-text="statusText"
              :can-start="canStart"
              :can-interrupt="canInterrupt"
              :error-message="errorMessage"
              :notice-message="noticeMessage"
              :mic-level="micLevel"
              :sent-frames="sentFrames"
              :devices="devices"
              :selected-device-id="selectedDeviceId"
              :route="selectedRoute"
              :routes="KB_ROUTE_OPTIONS"
              :mode-label="modeLabel"
              :model-label="modelLabel"
              :log-path="logPath"
              :show-text-input="showTextInput"
              @device-change="onDeviceChange"
              @route-change="onRouteChange"
              @start="onStart"
              @stop="stop"
              @interrupt="interrupt"
            />
          </div>

          <div class="kb-column">
            <TranscriptPanel
              :messages="messages"
              :show-composer="showTextInput"
              :can-send="canStart"
              @text-submit="onTextSubmit"
            />
            <div ref="bottomRef" class="kb-bottom" aria-hidden="true"></div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
