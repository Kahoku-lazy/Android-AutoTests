<script setup>
import { onMounted, nextTick, watch } from "vue"

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },

  icon: { type: String, default: "" },

  iconGradient: {
    type: String,
    default: "linear-gradient(135deg,var(--c-workflow),var(--wb-icon-gradient-end))",
  },
})

function refreshIcons() {
  if (props.icon && window.lucide) window.lucide.createIcons()
}

onMounted(async () => {
  await nextTick()
  refreshIcons()
})

watch(
  () => props.icon,
  async () => {
    await nextTick()
    refreshIcons()
  },
)
</script>

<template>
  <header class="wb-header">
    <div class="wb-header__row">
      <div class="brand">
        <span
          v-if="icon"
          class="brand-mark brand-mark--lucide"
          :style="{ background: iconGradient }"
        >
          <i :data-lucide="icon"></i>
        </span>
        <div class="brand-text">
          <h1 class="brand-title">{{ title }}</h1>
        </div>
      </div>
      <div v-if="$slots.actions" class="header-actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.wb-header {
  --wb-icon-gradient-end: var(--comp-wb-icon-gradient-end);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--app-space-xs);

  min-height: var(--app-topbar-h, 96px);
  box-sizing: border-box;
  padding: var(--app-space-sm) var(--app-space-lg);

  background: var(--paper);
  border-bottom: 2.5px solid var(--ink);
  flex-shrink: 0;

  position: relative;
  z-index: var(--z-header);
}
.wb-header__row {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  width: 100%;
  min-width: 0;
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
  font-size: var(--app-size-md);
  border-radius: 8px 16px 6px 14px;
  flex-shrink: 0;
  background: var(--app-highlight);
  border: 2.5px solid var(--ink);
  transform: rotate(-2deg);
}
.brand-mark--lucide {
  box-shadow: none;
}
.brand-mark--lucide :deep(svg) {
  width: 18px;
  height: 18px;
  color: var(--app-text-primary);
  stroke: var(--ink);
}
.brand-text {
  min-width: 0;
}
.brand-title {
  margin: 0;

  font-family: var(--app-font-brand);
  font-size: var(--app-size-xl);
  font-weight: var(--app-font-weight-regular);
  color: var(--app-text-primary);
  line-height: var(--app-line-height-tight);
  transform: rotate(-0.5deg);

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}

.wb-header :deep(.el-button) {
  font-weight: var(--app-font-weight-heavy) !important;
  border-width: 2.5px !important;
  border-radius: var(--app-radius-md) !important;
  padding: 5px 14px !important;
  font-family: inherit !important;
  transition: all var(--app-duration-fast) !important;
  box-shadow: none !important;
}
.wb-header :deep(.el-button:active) {
  transform: translate(1px, 1px) !important;
}
</style>
