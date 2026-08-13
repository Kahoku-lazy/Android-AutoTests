<script setup lang="ts">
import { formatConfirmArgs } from '../composables/useToolConfirm'
import type { HitlConfirmEvent } from '@/shared/types/ai'

defineProps<{ confirm?: HitlConfirmEvent | null }>()

const emit = defineEmits<{
  approve: [toolCallId: string]
  deny: [toolCallId: string]
  'approve-all': []
  'deny-all': []
  cancel: []
}>()
</script>

<template>
  <div v-if="confirm" class="confirm-overlay">
    <div class="confirm-dialog">
      <div class="confirm-header">
        <span class="confirm-icon">⚠️</span>
        <span class="confirm-title">操作需要确认</span>
      </div>
      <div class="confirm-body">
        <p class="confirm-desc">AI 助手请求执行以下敏感操作：</p>
        <div class="confirm-tools">
          <div
            v-for="tc in confirm.toolCalls"
            :key="tc.tool_call_id"
            class="confirm-tool-item"
          >
            <span class="confirm-tool-icon">🔧</span>
            <div class="confirm-tool-info">
              <span class="confirm-tool-name">{{ tc.tool_call_name }}</span>
              <pre class="confirm-tool-args">{{
                formatConfirmArgs(tc.arguments)
              }}</pre>
            </div>
            <div class="confirm-tool-actions">
              <button
                class="confirm-btn approve"
                @click="emit('approve', tc.tool_call_id)"
              >
                ✅ 允许
              </button>
              <button
                class="confirm-btn deny"
                @click="emit('deny', tc.tool_call_id)"
              >
                ❌ 拒绝
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="confirm-footer">
        <button class="confirm-btn approve-all" @click="emit('approve-all')">
          ✅ 全部允许
        </button>
        <button class="confirm-btn deny-all" @click="emit('deny-all')">
          ❌ 全部拒绝
        </button>
        <button class="confirm-btn cancel" @click="emit('cancel')">
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.confirm-dialog {
  background: var(--app-bg-card);
  border-radius: var(--app-radius-md);
  max-width: 560px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  animation: dialog-appear 0.2s ease;
}
@keyframes dialog-appear {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.confirm-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #fff8e1, #fff3e0);
  border-bottom: 2px solid #ffcc02;
}
.confirm-icon {
  font-size: var(--app-size-xl);
}
.confirm-title {
  font-size: var(--app-size-lg);
  font-weight: 700;
  color: #bf360c;
}
.confirm-body {
  padding: 20px 24px;
  max-height: 400px;
  overflow-y: auto;
}
.confirm-desc {
  font-size: var(--app-size-sm);
  color: #6d5f4b;
  margin: 0 0 14px;
}
.confirm-tools {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.confirm-tool-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border-radius: 10px;
  border: 1.5px solid var(--doodle-bg, #faf5ee);
  background: var(--ai-warm-bg);
}
.confirm-tool-icon {
  font-size: var(--app-size-lg);
  flex-shrink: 0;
  margin-top: 2px;
}
.confirm-tool-info {
  flex: 1;
  min-width: 0;
}
.confirm-tool-name {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--doodle-ink, #2d2d2d);
  display: block;
  margin-bottom: 6px;
}
.confirm-tool-args {
  font-size: var(--app-size-sm);
  color: #6d5f4b;
  background: var(--app-bg-card);
  border-radius: 8px;
  padding: 8px 10px;
  margin: 0;
  overflow-x: auto;
  max-height: 120px;
  font-family: var(--app-font-mono);
  white-space: pre;
}
.confirm-tool-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}
.confirm-btn {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1.5px solid;
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.confirm-btn.approve {
  background: var(--ai-bg-success);
  color: var(--app-status-success-text);
  border-color: var(--app-status-success);
}
.confirm-btn.approve:hover {
  background: var(--ai-bg-success-hover);
}
.confirm-btn.deny {
  background: var(--ai-bg-error);
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
}
.confirm-btn.deny:hover {
  background: var(--ai-bg-error-hover);
}
.confirm-btn.cancel {
  background: var(--ai-bg-neutral);
  color: var(--app-text-secondary);
  border-color: var(--app-offline);
}
.confirm-btn.cancel:hover {
  background: var(--ai-bg-neutral-hover);
}
.confirm-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: var(--ai-warm-bg);
  border-top: 1px solid var(--doodle-bg, #faf5ee);
  flex-wrap: wrap;
}
.confirm-btn.approve-all {
  background: var(--ai-teal-bg);
  color: var(--ai-teal-text);
  border-color: var(--app-accent-purple, #b39ef3);
  flex: 1;
  justify-content: center;
}
.confirm-btn.approve-all:hover {
  background: var(--ai-bg-teal-hover);
}
.confirm-btn.deny-all {
  background: var(--ai-bg-error);
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
  flex: 1;
  justify-content: center;
}
.confirm-btn.deny-all:hover {
  background: var(--ai-bg-error-hover);
}
</style>
