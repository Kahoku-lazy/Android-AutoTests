<script setup lang="ts">
import { ref } from 'vue'
import { IconSend, IconPaperclip, IconImage } from '@/shared/icons/index'

export type PendingImage = {
  filename: string
  size: number
  media_type: string
  data_uri: string
}

const props = defineProps<{
  modelValue?: string
  sending?: boolean
  uploadedFile?: { filename?: string; name?: string; size: number } | null
  uploadedImage?: PendingImage | null
  uploading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  stop: []
  keydown: [e: KeyboardEvent]
  upload: [e: Event]
  'upload-image': [e: Event]
  'remove-file': []
  'remove-image': []
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const imageInputRef = ref<HTMLInputElement | null>(null)

function onInput(val: string | number) {
  emit('update:modelValue', String(val))
}

function onPrimaryClick() {
  if (props.sending) emit('stop')
  else emit('send')
}
</script>

<template>
  <div v-if="uploadedImage" class="file-preview image-preview">
    <el-image
      class="image-preview-thumb"
      :src="uploadedImage.data_uri"
      :preview-src-list="[uploadedImage.data_uri]"
      fit="cover"
    />
    <span class="file-preview-name">{{ uploadedImage.filename }}</span>
    <span class="file-preview-size">
      ({{ (uploadedImage.size / 1024).toFixed(1) }} KB)
    </span>
    <button class="file-preview-remove" @click="emit('remove-image')">✕</button>
  </div>
  <div v-else-if="uploadedFile" class="file-preview">
    <span class="file-preview-icon">
      <IconPaperclip :size="14" />
    </span>
    <span class="file-preview-name">{{ uploadedFile.filename || uploadedFile.name }}</span>
    <span class="file-preview-size">
      ({{ (uploadedFile.size / 1024).toFixed(1) }} KB)
    </span>
    <button class="file-preview-remove" @click="emit('remove-file')">✕</button>
  </div>

  <div class="chat-input">
    <input
      ref="fileInputRef"
      type="file"
      accept=".txt,.log,.md,.json,.xml,.csv,.py,.js,.html,.css,.yaml,.yml,.docx,.xlsx,.pdf"
      style="display: none"
      @change="emit('upload', $event)"
    />
    <input
      ref="imageInputRef"
      type="file"
      accept="image/png,image/jpeg,image/webp,image/gif"
      style="display: none"
      @change="emit('upload-image', $event)"
    />
    <button
      class="upload-btn"
      :disabled="sending || uploading"
      title="上传文件 (txt/log/md/docx/xlsx/pdf 等)"
      @click="fileInputRef?.click()"
    >
      <IconPaperclip :size="18" />
    </button>
    <button
      class="upload-btn"
      :disabled="sending || uploading"
      title="上传图片 (png/jpg/webp/gif，最大 5MB)"
      @click="imageInputRef?.click()"
    >
      <IconImage :size="18" />
    </button>
    <div class="input-box">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
        :disabled="sending"
        resize="none"
        @update:model-value="(v: string | number) => onInput(String(v))"
        @keydown="emit('keydown', $event as KeyboardEvent)"
      />
    </div>
    <button
      :class="['send-btn', { 'is-stop': sending }]"
      :disabled="!sending && !modelValue?.trim() && !uploadedFile && !uploadedImage"
      :title="sending ? '停止生成' : '发送'"
      @click="onPrimaryClick"
    >
      <template v-if="sending">
        <span class="stop-square" aria-hidden="true" />
        <span>停止</span>
      </template>
      <template v-else>
        <IconSend :size="16" />
        <span>发送</span>
      </template>
    </button>
  </div>
</template>

<style scoped>
.file-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--app-bg-card);
  border-top: 1px solid var(--ink);
  font-size: var(--app-size-sm);
}
.image-preview-thumb {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 1px solid var(--ink);
  flex-shrink: 0;
  overflow: hidden;
}
.file-preview-icon {
  display: inline-flex;
  color: var(--el-color-primary);
}
.file-preview-name {
  font-weight: 600;
  color: var(--ink);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-preview-size {
  color: var(--app-ink-muted);
  font-size: var(--app-size-sm);
}
.file-preview-remove {
  background: none;
  border: none;
  color: var(--app-ink-muted);
  cursor: pointer;
  font-size: var(--app-size-sm);
  padding: 4px 8px;
  border-radius: 6px;
}
.file-preview-remove:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--app-error);
}
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 10px 16px 12px;
  background: var(--app-bg-card);
  border-top: 1px solid var(--ink);
  flex-shrink: 0;
}
.chat-input :deep(.el-textarea__inner) {
  border-radius: var(--app-radius-sm) !important;
  border: 1.5px solid var(--ink) !important;
  padding: 8px 12px !important;
  font-size: var(--app-size-sm) !important;
  line-height: 1.35 !important;
  min-height: 40px !important;
  background: var(--app-bg-input) !important;
  box-shadow: none !important;
  font-family: inherit !important;
  color: var(--ink) !important;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary) !important;
  background: rgba(255, 255, 255, 0.85) !important;
}
.upload-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--app-radius-sm);
  border: 1.5px solid var(--ink);
  background: var(--app-bg-card);
  color: var(--app-ink-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--app-duration-fast) var(--app-ease);
}
.upload-btn:hover:not(:disabled) {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.input-box {
  flex: 1;
  min-width: 0;
}
.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border-radius: var(--app-radius-sm);
  border: none;
  background: linear-gradient(
    135deg,
    var(--el-color-primary),
    var(--el-color-primary-dark-2)
  );
  color: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--app-duration-fast) var(--app-ease);
  box-shadow: var(--app-shadow-sm);
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--app-shadow-md);
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.send-btn.is-stop {
  background: linear-gradient(135deg, #e85f5f, #c43f3f);
  box-shadow: 0 2px 8px rgba(196, 63, 63, 0.25);
}
.send-btn.is-stop:hover:not(:disabled) {
  filter: brightness(1.05);
}
.stop-square {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: var(--app-bg-card);
  flex-shrink: 0;
}
</style>
