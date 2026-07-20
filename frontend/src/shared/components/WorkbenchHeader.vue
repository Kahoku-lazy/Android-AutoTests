<script setup>
/**
 * 业务模块工作台顶栏 — 对齐 workflow wb-header
 * actions 槽请放 el-button.wb-btn，勿用 animal Button
 */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  mark: { type: String, default: '🏝️' },
})
</script>

<template>
  <header class="wb-header">
    <div class="brand">
      <span class="brand-mark">{{ mark }}</span>
      <div class="brand-text">
        <h1 class="brand-title">{{ title }}</h1>
        <p v-if="subtitle || $slots.subtitle" class="brand-sub">
          <slot name="subtitle">{{ subtitle }}</slot>
        </p>
      </div>
    </div>
    <div v-if="$slots.actions" class="header-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.wb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: rgba(255, 251, 245, 0.95);
  border-bottom: 2px solid var(--ac-border, rgba(139, 115, 85, 0.16));
  flex-shrink: 0;
  z-index: 10;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.brand-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  font-size: 22px;
  background: linear-gradient(145deg, var(--app-green), var(--app-green-deep));
  border-radius: 14px;
  border: 1.5px solid rgba(142,200,160,0.25);
  flex-shrink: 0;
}
.brand-text { min-width: 0; }
.brand-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--ac-ink, #4a3a28);
  line-height: 1.25;
}
.brand-sub {
  margin: 2px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--ac-ink-faint, #988b7a);
  line-height: 1.35;
}
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
