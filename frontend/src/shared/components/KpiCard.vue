<script setup>
/**
 * KpiCard — Doodle Craft 统计数字卡片
 *
 * label 在上，数字在下。color + shape 四个卡片各不同，一眼识别。
 * shape: diamond | triangle | square | circle
 */
defineProps({
  value: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  color: { type: String, default: 'var(--c-dashboard)' },
  shape: { type: String, default: 'diamond' },
})

defineEmits(['click'])
</script>

<template>
  <div class="kpi-card" @click="$emit('click')">
    <div
      class="kpi-card__shape"
      :class="`kpi-card__shape--${shape}`"
      :style="{ background: color }"
    >
      <span v-if="shape !== 'circle'" class="kpi-card__shape-inner" />
    </div>
    <div class="kpi-card__label" :style="{ color: color }">{{ label }}</div>
    <div class="kpi-card__value">{{ value }}</div>
    <slot />
  </div>
</template>

<style scoped>
.kpi-card {
  text-align: center; padding: 18px 20px 14px; background: #fff;
  border: 3px solid var(--ink); border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-sm); position: relative;
  min-width: 120px; overflow: hidden;
}
.kpi-card::after {
  content: '~'; position: absolute; bottom: 2px; right: 8px;
  font-family: var(--app-font-display); font-size: 17px; opacity: 0.12;
}

/* ── 几何图形 — Doodle Craft 不对称几何 ── */
.kpi-card__shape {
  width: 22px; height: 22px; margin: 0 auto 10px;
  border: 2.5px solid var(--ink);
  display: flex; align-items: center; justify-content: center;
}
.kpi-card__shape-inner {
  width: 6px; height: 6px; background: #fff; border-radius: 1px;
}
/* 菱形 */
.kpi-card__shape--diamond { transform: rotate(45deg); }
.kpi-card__shape--diamond .kpi-card__shape-inner { transform: rotate(0deg); }
/* 三角 */
.kpi-card__shape--triangle {
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  border: none; width: 24px; height: 20px;
}
.kpi-card__shape--triangle .kpi-card__shape-inner {
  width: 5px; height: 5px; margin-top: 4px;
}
/* 方块 */
.kpi-card__shape--square { border-radius: 3px 6px 3px 6px; }
/* 圆 */
.kpi-card__shape--circle { border-radius: 50%; }
.kpi-card__shape--circle .kpi-card__shape-inner { display: none; }

/* ── 标签 ── */
.kpi-card__label {
  font-size: var(--app-size-sm); font-weight: 700;
  letter-spacing: 0.04em; margin-bottom: 2px;
}

/* ── 数字 ── */
.kpi-card__value {
  font-family: var(--app-font); font-size: var(--app-size-2xl);
  font-weight: 800; color: var(--ink); line-height: 1.1;
}
</style>
