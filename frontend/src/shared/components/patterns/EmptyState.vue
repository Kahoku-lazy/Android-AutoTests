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
  padding: 48px 24px;
  color: #988b7a;
  text-align: center;
  gap: 8px;
}
.empty-state__icon { font-size: 40px; line-height: 1.2; }
.empty-state__text { font-size: 15px; font-weight: 600; color: #4a3a28; margin: 0; }
.empty-state__hint { font-size: 13px; margin: 0; }
.empty-state__cta { margin-top: 12px; }
</style>
