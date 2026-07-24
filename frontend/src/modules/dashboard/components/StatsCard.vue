<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { countUpFormatted } from '@/shared/animations.js'
import { MODULE_COLORS } from '@/shared/constants/module-colors.js'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  desc: { type: String, default: '' },
  trend: { type: Number, default: 0 },
  trendLabel: { type: String, default: '' },
  /** app-green | app-blue | app-yellow | app-pink | app-teal | purple */
  color: { type: String, default: 'app-teal' },
  path: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const router = useRouter()
const valueRef = ref(null)
const displayed = ref(false)

const colorKey = computed(() => props.color.replace(/^app-/, ''))

const theme = computed(() => MODULE_COLORS[colorKey.value] || MODULE_COLORS.teal)

const metaText = computed(() => {
  if (props.trend !== 0 && props.trendLabel) {
    const arrow = props.trend > 0 ? '↑' : '↓'
    return `${arrow}${Math.abs(props.trend)}% ${props.trendLabel}`
  }
  if (props.trendLabel) return props.trendLabel
  if (props.desc) return props.desc
  return ''
})

watch(() => props.value, (newVal) => {
  if (valueRef.value && displayed.value) {
    countUpFormatted(valueRef.value, 0, newVal, 800, props.prefix, props.suffix)
  }
})

function onCardEnter() {
  if (!displayed.value) {
    displayed.value = true
    setTimeout(() => {
      if (valueRef.value) {
        countUpFormatted(valueRef.value, 0, props.value, 1200, props.prefix, props.suffix)
      }
    }, 200)
  }
}

function navigate() {
  if (props.path) router.push(props.path)
}
</script>

<template>
  <div
    class="stats-card"
    :class="[
      'stats-card--' + colorKey,
      { 'is-clickable': !!path },
    ]"
    @mouseenter="onCardEnter"
    @click="navigate"
  >
    <div v-if="loading" class="stats-card__skeleton">
      <div class="skeleton-bar skeleton-bar--icon"></div>
      <div class="skeleton-bar skeleton-bar--value"></div>
      <div class="skeleton-bar skeleton-bar--label"></div>
      <div class="skeleton-bar skeleton-bar--footer"></div>
    </div>

    <template v-else>
      <div
        class="stats-card__icon"
        :style="{ background: theme.gradient }"
      >
        <slot name="icon">
          <div class="stats-card__icon-placeholder"></div>
        </slot>
      </div>

      <div class="stats-card__title">{{ label }}</div>
      <div class="stats-card__desc">{{ desc || '核心指标实时更新' }}</div>

      <div class="stats-card__footer">
        <div class="stats-card__stat">
          <strong ref="valueRef">{{ prefix }}{{ value.toLocaleString() }}{{ suffix }}</strong>
          <small v-if="metaText">{{ metaText }}</small>
        </div>
        <button
          v-if="path"
          type="button"
          class="stats-card__enter"
          :style="{ background: theme.gradient }"
          @click.stop="navigate"
        >
          进入
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════
   Paper × Polaroid — 拍立得统计卡片
   ═══════════════════════════════════════════ */
.stats-card {
  background: #fff;
  border-radius: 6px 10px 6px 10px;
  padding: 8px 8px 36px 8px;
  border: 2.5px solid var(--ink);
  box-shadow: 2px 3px 0 rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.25s, transform 0.25s;
  position: relative;
  overflow: visible;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  cursor: pointer;
}

/* 图钉 */
.stats-card::before {
  content: '';
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 9px;
  height: 9px;
  background: radial-gradient(circle, #e8e0d5 30%, #c0b8a8 60%, #a09080 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.08);
  z-index: 2;
}

.stats-card:hover {
  box-shadow: 2px 4px 0 rgba(0, 0, 0, 0.08);
  transform: rotate(0deg) scale(1.03);
  z-index: 10;
}

/* 彩色照片区 */
.stats-card__icon {
  height: 60px;
  border-radius: 3px 5px 3px 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: 8px;
  position: relative;
  border: 2px solid var(--ink);
  box-shadow: none;
  width: auto;
}
/* 模块色映射为照片底色 */
.stats-card--green .stats-card__icon { background: var(--app-status-success-bg); }
.stats-card--blue .stats-card__icon  { background: var(--app-status-purple-bg); }
.stats-card--yellow .stats-card__icon{ background: var(--app-status-warning-bg); }
.stats-card--pink .stats-card__icon  { background: var(--app-status-danger-bg); }
.stats-card--teal .stats-card__icon  { background: #D4F5F0; }
.stats-card--purple .stats-card__icon{ background: #F0E8FF; }
.stats-card--orange .stats-card__icon{ background: #FFE8D0; }

.stats-card__icon :deep(svg) {
  width: 22px;
  height: 22px;
  color: var(--ink);
  stroke: var(--ink);
}

.stats-card__icon-placeholder {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.08);
}

.stats-card__title {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink);
  text-align: center;
  line-height: 1.3;
}

.stats-card__desc {
  font-size: 9px;
  color: var(--app-ink-muted);
  text-align: center;
  line-height: 1.4;
  margin-bottom: 8px;
  flex: 0;
}

.stats-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: auto;
  padding: 0 4px;
}

.stats-card__stat {
  min-width: 0;
}

.stats-card__stat strong {
  display: block;
  font-family: var(--doodle-font-title);
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1;
}

.stats-card__stat small {
  display: block;
  margin-top: 2px;
  font-size: 9px;
  font-weight: 700;
  color: var(--app-ink-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats-card__enter {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 800;
  color: var(--ink);
  padding: 4px 10px;
  border-radius: 4px 8px 4px 8px;
  border: 2px solid var(--ink);
  cursor: pointer;
  transition: all 0.12s;
  font-family: inherit;
  line-height: 1.2;
  background: #fff;
}
.stats-card__enter:hover {
  background: var(--app-highlight);
}

/* Skeleton */
.stats-card__skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0;
}
.skeleton-bar {
  background: linear-gradient(90deg, rgba(0,0,0,0.03) 25%, rgba(0,0,0,0.06) 50%, rgba(0,0,0,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
  border-radius: 4px;
}
.skeleton-bar--icon { width: 100%; height: 60px; border-radius: 3px 5px 3px 5px; }
.skeleton-bar--value { width: 55%; height: 24px; }
.skeleton-bar--label { width: 80%; height: 12px; }
.skeleton-bar--footer { width: 100%; height: 24px; margin-top: 2px; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .stats-card { transition: none; }
  .stats-card:hover { transform: none; }
  .skeleton-bar { animation: none; }
}
</style>
