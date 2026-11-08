<script setup lang="ts">
/**
 * 知识库助手页面：语音（Omni）或文字（DeepSeek Flash）问答 + 对话记录 + 本地日志落点。
 *
 * 页面只做三态取数与事件编排；音频、WS 与消息归并分别在 audio/、
 * composables/ 与 helpers/ 中。两种方式共享同一条 WS 与同一份日志。
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
import { useAssistantSession } from "./composables/useAssistantSession"
import { fetchKnowledgeAssistantStatus } from "./api"
import {
  KB_HINT_TEXT,
  KB_ICON_GRADIENT,
  KB_MODE_SWITCH_HINT,
  KB_MODE_TEXT,
  KB_PAGE_ICON,
  KB_PAGE_SUBTITLE,
  KB_PAGE_TITLE,
  KB_READY_FALLBACK,
  KB_STATUS_LOAD_ERROR,
  KB_TEXT_HINT,
  KB_TEXT_PLACEHOLDER,
  KB_TEXT_READY_FALLBACK,
} from "./constants"
import { modeLabel, statusTextFor } from "./helpers/mode"
import type { AssistantMode, KnowledgeAssistantStatus } from "./types"

const status = ref<KnowledgeAssistantStatus | null>(null)
const statusError = ref("")
const loading = ref(true)
const modeNotice = ref("")
const bottomRef = ref<HTMLElement | null>(null)

const {
  messages,
  state,
  mode,
  canType,
  errorMessage,
  noticeMessage,
  session,
  micLevel,
  sentFrames,
  devices,
  selectedDeviceId,
  loadDevices,
  isActive,
  canInterrupt,
  start,
  stop,
  interrupt,
  submitText,
  dispose,
} = useAssistantSession()

const canStart = computed(() =>
  mode.value === KB_MODE_TEXT ? status.value?.text_ready === true : status.value?.ready === true,
)
const statusText = computed(() => statusTextFor(mode.value, state.value))
const modeName = computed(() => modeLabel(mode.value))
const modelLabel = computed(() => {
  if (session.value) {
    return session.value.voice
      ? `${session.value.model} · ${session.value.voice}`
      : session.value.model
  }
  if (mode.value === KB_MODE_TEXT) return status.value?.text_model || "—"
  return status.value ? `${status.value.model} · ${status.value.voice}` : "—"
})
const logPath = computed(
  () => session.value?.logPath || status.value?.log_file || status.value?.log_dir || "—",
)
const unavailableReason = computed(() =>
  mode.value === KB_MODE_TEXT
    ? status.value?.text_reason || KB_TEXT_READY_FALLBACK
    : status.value?.reason || KB_READY_FALLBACK,
)
const unavailableHint = computed(() =>
  mode.value === KB_MODE_TEXT
    ? "按上面的原因处理后点击「重试」，文字入口才可用。"
    : "按上面的原因处理后点击「重试」，就绪后语音按键才可用。",
)
const hint = computed(() => (mode.value === KB_MODE_TEXT ? KB_TEXT_HINT : KB_HINT_TEXT))
const composerPlaceholder = KB_TEXT_PLACEHOLDER
/** 文字方式直接发送即可建连，但仍要先满足就绪状态（服务未就绪时输入框保持禁用） */
const canSendNow = computed(() => canType.value && canStart.value)
const mergedNotice = computed(() => modeNotice.value || noticeMessage.value)

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
  modeNotice.value = ""
  void start(mode.value)
}

function onModeChange(next: AssistantMode): void {
  if (isActive.value) {
    modeNotice.value = KB_MODE_SWITCH_HINT
    return
  }
  modeNotice.value = ""
  mode.value = next
}

function onDeviceChange(deviceId: string): void {
  selectedDeviceId.value = deviceId
}

function onTextSubmit(text: string): void {
  modeNotice.value = ""
  submitText(text)
}

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
      :subtitle="KB_PAGE_SUBTITLE"
      :icon="KB_PAGE_ICON"
      :icon-gradient="KB_ICON_GRADIENT"
    />

    <div class="doc-body kb-body">
      <SkeletonCard v-if="loading" variant="list" :lines="6" />

      <ErrorState v-else-if="statusError" :message="statusError" @retry="loadStatus" />

      <template v-else>
        <ErrorState v-if="!canStart" :message="unavailableReason" @retry="loadStatus" />
        <p v-if="!canStart" class="kb-notice-hint">
          {{ unavailableHint }}
        </p>

        <div class="kb-layout">
          <div class="kb-console-wrap">
            <VoiceConsole
              :mode="mode"
              :state="state"
              :status-text="statusText"
              :can-start="canStart"
              :can-interrupt="canInterrupt"
              :error-message="errorMessage"
              :notice-message="mergedNotice"
              :mic-level="micLevel"
              :sent-frames="sentFrames"
              :devices="devices"
              :selected-device-id="selectedDeviceId"
              :mode-label="modeName"
              :model-label="modelLabel"
              :log-path="logPath"
              :hint="hint"
              @device-change="onDeviceChange"
              @mode-change="onModeChange"
              @start="onStart"
              @stop="stop"
              @interrupt="interrupt"
            />
          </div>

          <div class="kb-column">
            <TranscriptPanel
              :messages="messages"
              :show-composer="mode === KB_MODE_TEXT"
              :can-send="canSendNow"
              :placeholder="composerPlaceholder"
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
