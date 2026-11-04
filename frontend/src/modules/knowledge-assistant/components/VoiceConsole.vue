<script setup lang="ts">
/**
 * 语音/文字控制台：方式选择、圆形语音按键或打字提示、状态与日志落点。
 *
 * 组件只负责渲染与事件绑定；会话状态由 useAssistantSession 提供。
 */
import { computed, nextTick, onMounted, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import {
  KB_INTERRUPT_LABEL,
  KB_MIC_ACTIVE,
  KB_MIC_IDLE,
  KB_MIC_WAITING,
  KB_MODE_OPTIONS,
  KB_MODE_VOICE,
  KB_START_LABEL,
  KB_STOP_LABEL,
} from "../constants"
import type { MicrophoneDevice } from "../audio/micCapture"
import type { AssistantMode, VoiceState } from "../types"

const props = defineProps<{
  mode: AssistantMode
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
  modeLabel: string
  modelLabel: string
  logPath: string
  hint: string
}>()

const emit = defineEmits<{
  start: []
  stop: []
  interrupt: []
  deviceChange: [deviceId: string]
  modeChange: [mode: AssistantMode]
}>()

const isVoice = computed(() => props.mode === KB_MODE_VOICE)
const isActive = computed(() => props.state !== "idle" && props.state !== "error")
const buttonTitle = computed(() => (isActive.value ? KB_STOP_LABEL : KB_START_LABEL))
const levelPercent = computed(() => Math.min(100, Math.round(props.micLevel * 400)))
const micStatusText = computed(() => {
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

onMounted(async () => {
  await nextTick()
  refreshIcons()
})

watch(
  () => [props.state, props.mode],
  async () => {
    await nextTick()
    refreshIcons()
  },
)
</script>

<template>
  <section class="kb-console" data-testid="kb-console">
    <div class="kb-modes" role="group" aria-label="会话方式">
      <button
        v-for="option in KB_MODE_OPTIONS"
        :key="option.value"
        type="button"
        class="kb-mode-btn"
        :class="{ 'is-active': option.value === mode }"
        :aria-pressed="option.value === mode"
        :data-testid="`kb-mode-${option.value}`"
        @click="emit('modeChange', option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="kb-stage">
      <label v-if="isVoice" class="kb-device">
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

      <div
        v-if="isVoice"
        class="kb-orb"
        :class="{ 'is-active': isActive, 'is-speaking': state === 'speaking' }"
      >
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
      <div v-else class="kb-text-stage" data-testid="kb-text-stage">
        <i data-lucide="message-square-text"></i>
      </div>

      <p class="kb-status" :class="`kb-status--${state}`" data-testid="kb-status">
        {{ statusText }}
      </p>
      <p v-if="noticeMessage" class="kb-notice" data-testid="kb-notice">
        {{ noticeMessage }}
      </p>
      <p v-if="errorMessage" class="kb-error" data-testid="kb-error">{{ errorMessage }}</p>
      <p class="kb-hint">{{ hint }}</p>
      <div v-if="isActive && isVoice" class="kb-mic" data-testid="kb-mic">
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
        v-if="canInterrupt && isVoice"
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
        <dd data-testid="kb-mode-label">{{ modeLabel }}</dd>
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
