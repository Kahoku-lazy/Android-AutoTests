<script setup lang="ts">
import { IconSend, IconPaperclip } from '@/shared/icons/index'

defineProps<{
  modelValue?: string
  sending?: boolean
  uploadedFile?: { name: string; size: number } | null
  uploading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  keydown: [e: KeyboardEvent]
  upload: []
  'remove-file': []
}>()

function onInput(val: string) {
  emit('update:modelValue', val)
}
</script>

<template>
  <div v-if="uploadedFile" class="file-preview">
    <span class="file-preview-icon">
      <IconPaperclip :size="14" />
    </span>
    <span class="file-preview-name">{{ uploadedFile.filename }}</span>
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
    <button
      class="upload-btn"
      :disabled="sending || uploading"
      title="上传文件 (txt/log/md/docx/xlsx/pdf 等)"
      @click="$refs.fileInputRef?.click()"
    >
      <IconPaperclip :size="18" />
    </button>
    <div class="input-box">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :rows="2"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
        :disabled="sending"
        resize="none"
        @update:model-value="onInput"
        @keydown="emit('keydown', $event)"
      />
    </div>
    <button
      class="send-btn"
      :disabled="(!modelValue.trim() && !uploadedFile) || sending"
      @click="emit('send')"
    >
      <IconSend :size="16" />
      <span>{{ sending ? "发送中" : "发送" }}</span>
    </button>
  </div>
</template>

<style scoped>
.file-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
  border-top: 1px solid var(--ink);
  font-size: var(--app-size-sm);
  
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
  color: #999;
  font-size: var(--app-size-sm);
}
.file-preview-remove {
  background: none;
  border: none;
  color: #999;
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
  background: #fff;
  border-top: 1px solid var(--ink);
  flex-shrink: 0;
  
}
.chat-input :deep(.el-textarea__inner) {
  border-radius: var(--app-radius-sm) !important;
  border: 1.5px solid var(--ink) !important;
  padding: 8px 12px !important;
  font-size: var(--app-size-sm) !important;
  line-height: 1.45 !important;
  min-height: 44px !important;
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
  background: #fff;
  color: #999;
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
  color: #fff;
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
</style>
