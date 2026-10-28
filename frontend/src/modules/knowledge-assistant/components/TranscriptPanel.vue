<script setup lang="ts">
/**
 * 对话记录面板：按角色渲染消息、流式状态与打断标记。
 *
 * 面板本身不滚动；纵向滚动留在页面 .doc-body。
 */
import { ref } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import {
  KB_EMPTY_HINT,
  KB_EMPTY_TITLE,
  KB_MSG_ANSWERING,
  KB_MSG_ERROR,
  KB_MSG_INTERRUPTED,
  KB_MSG_PLACEHOLDER,
  KB_MSG_RECOGNIZING,
  KB_ROLE_ASSISTANT,
  KB_ROLE_USER,
} from "../constants"
import type { MessageRole, TranscriptMessage } from "../types"

defineProps<{
  messages: TranscriptMessage[]
  showComposer: boolean
  canSend: boolean
}>()

const emit = defineEmits<{
  textSubmit: [text: string]
}>()

const textValue = ref("")

function onTextSubmit() {
  const text = textValue.value.trim()
  if (!text) return
  textValue.value = ""
  emit("textSubmit", text)
}

function roleLabel(role: MessageRole): string {
  return role === "user" ? KB_ROLE_USER : KB_ROLE_ASSISTANT
}

function statusLabel(message: TranscriptMessage): string {
  if (message.status === "interrupted") return KB_MSG_INTERRUPTED
  if (message.status === "error") return KB_MSG_ERROR
  if (message.status === "streaming") {
    return message.role === "user" ? KB_MSG_RECOGNIZING : KB_MSG_ANSWERING
  }
  return ""
}
</script>

<template>
  <section class="kb-transcript-panel" data-testid="kb-transcript">
    <header class="kb-panel-head">
      <h2 class="kb-panel-title">对话记录</h2>
      <span class="kb-panel-count">{{ messages.length }} 条</span>
    </header>

    <div class="kb-transcript">
      <EmptyState
        v-if="messages.length === 0"
        icon="🎙️"
        :text="KB_EMPTY_TITLE"
        :hint="KB_EMPTY_HINT"
      />
      <article
        v-for="message in messages"
        :key="message.id"
        class="kb-msg"
        :class="[`kb-msg--${message.role}`, `kb-msg--${message.status}`]"
      >
        <div class="kb-msg__meta">
          <span class="kb-msg__role">{{ roleLabel(message.role) }}</span>
          <span
            v-if="statusLabel(message)"
            class="kb-msg__status"
            :class="`kb-msg__status--${message.status}`"
          >
            {{ statusLabel(message) }}
          </span>
        </div>
        <p class="kb-msg__text">{{ message.text || KB_MSG_PLACEHOLDER }}</p>
      </article>
    </div>

    <form
      v-if="showComposer"
      class="kb-composer"
      data-testid="kb-text-form"
      @submit.prevent="onTextSubmit"
    >
      <input
        v-model="textValue"
        class="kb-composer__input"
        data-testid="kb-text-input"
        type="text"
        placeholder="输入文字提问，例如：长按开关按键3秒会怎样？"
        :disabled="!canSend"
      />
      <DoodleBtn
        tone="teal"
        type="submit"
        data-testid="kb-text-send"
        :disabled="!canSend || !textValue.trim()"
      >
        发送
      </DoodleBtn>
    </form>
  </section>
</template>

<style src="./TranscriptPanel.style.css" scoped></style>
