<script setup>
import { sanitizeHtml } from "../composables/useMarkdown.js";

defineProps({
  thinking: { type: String, default: "" },
  thinkingDone: { type: Boolean, default: false },
  expanded: { type: Boolean, default: false },
});

const emit = defineEmits(["toggle"]);
</script>

<template>
  <div
    class="thinking-block"
    :class="{ 'thinking-done': thinkingDone }"
  >
    <div class="thinking-header" @click="emit('toggle')">
      <span class="thinking-icon">{{ thinkingDone ? "💭" : "🤔" }}</span>
      <span class="thinking-label">思考过程</span>
      <span class="thinking-toggle">{{ expanded ? "收起" : "展开" }}</span>
    </div>
    <div
      v-if="expanded || !thinkingDone"
      class="thinking-body"
      v-html="sanitizeHtml(thinking)"
    />
  </div>
</template>

<style scoped>
.thinking-block {
  margin: 4px 0;
  border-radius: 12px;
  border: 1px solid #d6c9a8;
  background: rgba(230, 222, 198, 0.15);
  overflow: hidden;
}
.thinking-block.thinking-done {
  border-color: #c9be9e;
  background: rgba(230, 222, 198, 0.08);
}
.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 13px;
  color: #8a7b66;
  user-select: none;
}
.thinking-icon {
  font-size: 14px;
}
.thinking-label {
  font-weight: 700;
}
.thinking-toggle {
  font-size: 11px;
  color: #b5a68e;
  margin-left: auto;
}
.thinking-body {
  padding: 10px 14px;
  font-size: 13px;
  line-height: 1.6;
  color: #6d5f4b;
  border-top: 1px solid #d6c9a8;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}
.thinking-block:not(.thinking-done) .thinking-header {
  color: #19c8b9;
}
.thinking-block:not(.thinking-done) .thinking-icon {
  animation: pulse 1.2s infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}
</style>
