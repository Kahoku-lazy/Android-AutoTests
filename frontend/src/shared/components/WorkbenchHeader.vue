<script setup>
/**
 * 业务模块工作台顶栏 — 对齐 workflow wb-header
 * actions 槽请放 el-button.wb-btn，勿用 animal Button
 * icon: Lucide 图标名（与 ModuleNavigator / 侧栏同步）；未传时回退 emoji mark
 */
import { onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  mark: { type: String, default: '🏝️' },
  /** Lucide 图标名，如 layout-dashboard；优先于 mark */
  icon: { type: String, default: '' },
  /** 图标底色渐变，与 module-nav 卡片一致 */
  iconGradient: {
    type: String,
    default: 'linear-gradient(135deg,var(--c-workflow),#60a5fa)',
  },
})

function refreshIcons() {
  if (props.icon && window.lucide) window.lucide.createIcons()
}

onMounted(async () => {
  await nextTick()
  refreshIcons()
})

watch(() => props.icon, async () => {
  await nextTick()
  refreshIcons()
})
</script>

<template>
  <header class="wb-header">
    <div class="brand">
      <span
        v-if="icon"
        class="brand-mark brand-mark--lucide"
        :style="{ background: iconGradient }"
      >
        <i :data-lucide="icon"></i>
      </span>
      <span v-else class="brand-mark soft-icon soft-icon--blue">{{ mark }}</span>
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
/* ═══════════════════════════════════════════
   Paper × Polaroid — 纸艺拍立得 Header
   ═══════════════════════════════════════════ */
.wb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  height: var(--app-topbar-h, 96px);
  box-sizing: border-box;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 2.5px solid var(--ink);
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
  font-size: 16px;
  border-radius: 8px 16px 6px 14px;
  flex-shrink: 0;
  background: #FFE066;
  border: 2.5px solid var(--ink);
  transform: rotate(-2deg);
}
.brand-mark--lucide {
  box-shadow: none;
}
.brand-mark--lucide :deep(svg) {
  width: 18px;
  height: 18px;
  color: var(--ink);
  stroke: var(--ink);
}
.brand-text { min-width: 0; }
.brand-title {
  margin: 0;
  font-family: var(--app-font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.2;
  transform: rotate(-0.5deg);
}
.brand-sub {
  margin: 1px 0 0;
  font-size: 11px;
  font-weight: 600;
  color: #999;
  line-height: 1.35;
}
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
/* Override .wb-btn in this header context */
.wb-header :deep(.el-button) {
  font-weight: 800 !important;
  color: var(--ink) !important;
  background: #fff !important;
  border: 2.5px solid var(--ink) !important;
  border-radius: 6px 12px 6px 12px !important;
  padding: 5px 14px !important;
  font-family: inherit !important;
  transition: all 0.12s !important;
  box-shadow: none !important;
}
.wb-header :deep(.el-button:hover) {
  background: #FFE066 !important;
}
.wb-header :deep(.el-button:active) {
  transform: translate(1px, 1px) !important;
}
</style>
