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
    default: 'linear-gradient(135deg,#89CFF0,#60a5fa)',
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
.wb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: rgba(255,255,255,0.52);
  border-bottom: 1px solid var(--ac-border, rgba(255,255,255,0.68));
  backdrop-filter: blur(var(--app-glass-blur, 20px));
  -webkit-backdrop-filter: blur(var(--app-glass-blur, 20px));
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
  border-radius: 14px;
  flex-shrink: 0;
}
.brand-mark--lucide {
  box-shadow: var(--app-icon-shadow, 0 10px 24px rgba(74, 78, 105, 0.12));
}
.brand-mark--lucide :deep(svg) {
  width: 20px;
  height: 20px;
  color: #fff;
  stroke: #fff;
}
.brand-text { min-width: 0; }
.brand-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--ac-ink, #4a4e69);
  line-height: 1.25;
}
.brand-sub {
  margin: 2px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--ac-ink-faint, #a8b5c4);
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
