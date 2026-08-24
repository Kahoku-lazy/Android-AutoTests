<template>
  <div class="empty-state">
    <span class="empty-state__icon" v-if="icon">{{ icon }}</span>
    <p class="empty-state__text">{{ text }}</p>
    <p class="empty-state__hint" v-if="hint">{{ hint }}</p>
    <div class="empty-state__cta" v-if="$slots.default">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  /** Emoji icon (e.g. "📁" "📋" "🔍") */
  icon: { type: String, default: '' },
  /** Primary text (e.g. "暂无页面" "没有匹配的结果") */
  text: { type: String, required: true },
  /** Secondary hint text */
  hint: { type: String, default: '' },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--app-space-2xl) var(--app-space-lg);
  color: var(--app-text-secondary);
  text-align: center;
  gap: var(--app-space-sm);
}
.empty-state__icon { font-size: 40px; line-height: 1.2; }
.empty-state__text { font-size: var(--app-size-md); font-weight: 700; color: var(--ink); margin: 0; }
.empty-state__hint { font-size: var(--app-size-sm); margin: 0; }
.empty-state__cta { margin-top: var(--app-space-md); }
</style>
