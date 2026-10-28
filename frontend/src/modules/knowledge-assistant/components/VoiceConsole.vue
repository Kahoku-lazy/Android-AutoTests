<script setup lang="ts">
/**
 * 语音控制台：圆形语音按键、状态、错误与日志落点。
 *
 * 组件只负责渲染与事件绑定；会话状态由 useVoiceSession 提供。
 */
import { computed, nextTick, onMounted, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import {
  KB_HINT_TEXT,
  KB_INTERRUPT_LABEL,
  KB_MIC_ACTIVE,
  KB_MIC_IDLE,
  KB_MIC_TEXT,
  KB_MIC_WAITING,
  KB_START_LABEL,
  KB_STOP_LABEL,
} from "../constants"
import type { MicrophoneDevice } from "../audio/micCapture"
import type { KbRoute } from "../constants"
import type { VoiceState } from "../types"

const props = defineProps<{
  state: VoiceState
  statusText: string
  canStart: boolean
  canInterrupt: boolean
  errorMessage: string
  noticeMessage: string
  micLevel: number
  sentFrames: number
  devices: MicrophoneDevice[]
  selectedDeviceId: string
  route: KbRoute
  routes: readonly { value: KbRoute; label: string }[]
  modeLabel: string
  modelLabel: string
  logPath: string
  showTextInput: boolean
}>()

const emit = defineEmits<{
  start: []
  stop: []
  interrupt: []
  deviceChange: [deviceId: string]
  routeChange: [route: KbRoute]
}>()

const isActive = computed(() => props.state !== "idle" && props.state !== "error")
const buttonTitle = computed(() => (isActive.value ? KB_STOP_LABEL : KB_START_LABEL))
const levelPercent = computed(() => Math.min(100, Math.round(props.micLevel * 400)))
const micStatusText = computed(() => {
  if (props.sentFrames === 0 && props.showTextInput && isActive.value) {
    return KB_MIC_TEXT
  }
  if (props.sentFrames === 0) return KB_MIC_IDLE
  if (props.micLevel < 0.005) return KB_MIC_WAITING
  return KB_MIC_ACTIVE
})

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons()
}

async function onVoiceClick() {
  if (isActive.value) emit("stop")
  else if (props.canStart) emit("start")
}

function onDeviceChange(event: Event) {
  emit("deviceChange", (event.target as HTMLSelectElement).value)
}

function onRouteChange(event: Event) {
  emit("routeChange", (event.target as HTMLSelectElement).value as KbRoute)
}

onMounted(async () => {
  await nextTick()
  refreshIcons()
})

watch(
  () => props.state,
  async () => {
    await nextTick()
    refreshIcons()
  },
)
</script>

<template>
  <section class="kb-console" data-testid="kb-console">
    <div class="kb-stage">
      <label class="kb-device">
        <span class="kb-device__label">路线</span>
        <select
          class="kb-device__select"
          data-testid="kb-route"
          :value="route"
          :disabled="isActive"
          @change="onRouteChange"
        >
          <option v-for="option in routes" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="kb-device">
        <span class="kb-device__label">麦克风</span>
        <select
          class="kb-device__select"
          data-testid="kb-device"
          :value="selectedDeviceId"
          :disabled="isActive"
          @change="onDeviceChange"
        >
          <option value="">系统默认</option>
          <option v-for="device in devices" :key="device.deviceId" :value="device.deviceId">
            {{ device.label }}
          </option>
        </select>
      </label>

      <div class="kb-orb" :class="{ 'is-active': isActive, 'is-speaking': state === 'speaking' }">
        <button
          type="button"
          class="kb-voice-btn"
          data-testid="kb-voice-btn"
          :class="{ 'is-active': isActive, 'is-speaking': state === 'speaking' }"
          :title="buttonTitle"
          :disabled="!isActive && !canStart"
          @click="onVoiceClick"
        >
          <i :data-lucide="isActive ? 'square' : 'mic'"></i>
        </button>
      </div>

      <p class="kb-status" :class="`kb-status--${state}`" data-testid="kb-status">
        {{ statusText }}
      </p>
      <p v-if="noticeMessage" class="kb-notice" data-testid="kb-notice">
        {{ noticeMessage }}
      </p>
      <p v-if="errorMessage" class="kb-error" data-testid="kb-error">{{ errorMessage }}</p>
      <p class="kb-hint">{{ KB_HINT_TEXT }}</p>
      <div v-if="isActive" class="kb-mic" data-testid="kb-mic">
        <span class="kb-mic__label">{{ micStatusText }}</span>
        <span class="kb-mic__meter">
          <span class="kb-mic__fill" :style="{ width: levelPercent + '%' }"></span>
        </span>
      </div>
    </div>

    <div class="kb-actions">
      <DoodleBtn
        v-if="!isActive"
        tone="teal"
        :disabled="!canStart"
        data-testid="kb-start"
        @click="emit('start')"
      >
        {{ KB_START_LABEL }}
      </DoodleBtn>
      <DoodleBtn v-else tone="danger" data-testid="kb-stop" @click="emit('stop')">
        {{ KB_STOP_LABEL }}
      </DoodleBtn>
      <DoodleBtn
        v-if="canInterrupt"
        tone="yellow"
        data-testid="kb-interrupt"
        @click="emit('interrupt')"
      >
        {{ KB_INTERRUPT_LABEL }}
      </DoodleBtn>
    </div>

    <dl class="kb-meta">
      <div class="kb-meta__row">
        <dt>模式</dt>
        <dd>{{ modeLabel }}</dd>
      </div>
      <div class="kb-meta__row">
        <dt>模型</dt>
        <dd>{{ modelLabel }}</dd>
      </div>
      <div class="kb-meta__row">
        <dt>日志</dt>
        <dd :title="logPath">{{ logPath }}</dd>
      </div>
    </dl>
  </section>
</template>

<style src="./VoiceConsole.style.css" scoped></style>
