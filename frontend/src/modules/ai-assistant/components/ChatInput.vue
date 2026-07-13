<script setup>
import { IconSend } from "@/shared/icons/index.js";

defineProps({
  modelValue: { type: String, default: "" },
  sending: { type: Boolean, default: false },
  uploadedFile: { type: Object, default: null },
  uploading: { type: Boolean, default: false },
});

const emit = defineEmits([
  "update:modelValue",
  "send",
  "keydown",
  "upload",
  "remove-file",
]);

function onInput(val) {
  emit("update:modelValue", val);
}
</script>

<template>
  <div v-if="uploadedFile" class="file-preview">
    <span class="file-preview-icon">📎</span>
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
      📎
    </button>
    <div class="input-box">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :rows="3"
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
      <IconSend :size="20" />
      <span>{{ sending ? "发送中" : "发送" }}</span>
    </button>
  </div>
</template>

<style scoped>
.file-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f5f3ed;
  border-top: 1px solid #e8e2d6;
  font-size: 13px;
}
.file-preview-icon {
  font-size: 16px;
}
.file-preview-name {
  font-weight: 600;
  color: #4a3a28;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-preview-size {
  color: #8a7b66;
  font-size: 12px;
}
.file-preview-remove {
  background: none;
  border: none;
  color: #8a7b66;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 6px;
}
.file-preview-remove:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #e85f5f;
}
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-top: 2px solid #e8e2d6;
  flex-shrink: 0;
}
.chat-input :deep(.el-textarea__inner) {
  border-radius: 14px !important;
  border: 2px solid #e8e2d6 !important;
  padding: 12px 16px !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
  background: #faf9f4 !important;
  box-shadow: none !important;
  font-family: inherit !important;
  color: #4a3a28 !important;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: #19c8b9 !important;
  background: #fff !important;
}
.upload-btn {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  border: 2px solid #e8e2d6;
  background: #faf9f4;
  font-size: 20px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.upload-btn:hover:not(:disabled) {
  border-color: #19c8b9;
  background: #e6f9f6;
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
  gap: 8px;
  padding: 12px 24px;
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #19c8b9, #15a89c);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
  box-shadow: 0 4px 14px rgba(25, 200, 185, 0.35);
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(25, 200, 185, 0.45);
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
