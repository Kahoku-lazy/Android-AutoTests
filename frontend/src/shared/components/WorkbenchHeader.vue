<script setup>
/**
 * 业务模块工作台顶栏 — 对齐 workflow wb-header
 * actions 槽请放 el-button.wb-btn，勿用 animal Button
 * icon: Lucide 图标名（与 ModuleNavigator / 侧栏同步），必须传；无 emoji 回退
 */
import { onMounted, nextTick, watch } from "vue"

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  /** Lucide 图标名，如 layout-dashboard；必须传（图标是页头的唯一标识块） */
  icon: { type: String, default: "" },
  /** 图标底色渐变，与 module-nav 卡片一致 */
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
          <p v-if="subtitle || $slots.subtitle" class="brand-sub">
            <slot name="subtitle">{{ subtitle }}</slot>
          </p>
        </div>
      </div>
      <div v-if="$slots.actions" class="header-actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<style scoped>
/* ═══════════════════════════════════════════
   Paper × Polaroid — 纸艺拍立得 Header
   ═══════════════════════════════════════════ */
.wb-header {
  /* 图标底色渐变末端（默认天蓝→亮蓝；本组件专用色值登记处） */
  --wb-icon-gradient-end: var(--comp-wb-icon-gradient-end);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--app-space-xs);
  /* 常规宽度 = --app-topbar-h（与侧栏 header 底边对齐）；动作区换行时靠 min-height 增高，
     把正文推开，而不是让内容溢出覆盖正文 */
  min-height: var(--app-topbar-h, 96px);
  box-sizing: border-box;
  padding: var(--app-space-sm) var(--app-space-lg);
  background: var(--app-bg-card);
  border-bottom: 2.5px solid var(--ink);
  flex-shrink: 0;
  /* 让下方 z-index 真正参与层叠（static 元素上的 z-index 无效） */
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
  color: var(--ink);
  stroke: var(--ink);
}
.brand-text {
  min-width: 0;
}
.brand-title {
  margin: 0;
  font-family: var(--app-font-display);
  font-size: var(--app-size-2xl);
  font-weight: 700;
  color: var(--ink);
  line-height: 1.2;
  transform: rotate(-0.5deg);
  /* 单行收敛：长标题不折行，超出省略号 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-sub {
  margin: 1px 0 0;
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-text-secondary);
  line-height: 1.35;
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
/* 页头按钮只做几何：颜色（含 hover 与语义色）交还主题层（workbench-theme.css / motion.css）。
   若在此处用 !important 强制 background / color / border，会把 primary / danger 与
   wb-btn--* 变体一并压成同一底色，丢失操作语义。
   border-width 必须保留：用于覆盖基础皮肤的 `border: 2px solid` 简写。 */
.wb-header :deep(.el-button) {
  font-weight: 800 !important;
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
