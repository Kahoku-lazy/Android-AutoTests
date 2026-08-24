<script setup>
/**
 * ErrorState — 通用错误提示条（含可选重试按钮）
 *
 * 替代每个模块手写的 <div v-if="error" class="xxx__error"> 模式。
 */
defineProps({
  message: { type: String, default: '加载失败' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="error-state">
    <span class="error-state__text">{{ message }}</span>
    <button class="error-state__btn" @click="$emit('retry')">
      <slot name="action">重试</slot>
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex; align-items: center; justify-content: center;
  gap: var(--app-space-md); padding: var(--app-space-sm) var(--app-space-lg); margin: 0 var(--app-space-lg);
  background: var(--app-error-bg, #fff0f0); border: 2px solid var(--app-status-danger);
  border-radius: var(--app-radius-md);
  font-size: var(--app-size-sm); color: var(--app-status-danger-text);
  font-weight: 600;
}
.error-state__btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: var(--app-space-xs) var(--app-space-md);
  border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  background: var(--app-bg-card); color: var(--ink); cursor: pointer;
  transition: all var(--app-duration-fast) var(--app-ease);
  font-family: var(--app-font);
}
.error-state__btn:hover {
  background: var(--app-highlight); transform: translate(1px,1px);
}
</style>
