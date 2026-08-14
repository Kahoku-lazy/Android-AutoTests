<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { countUpFormatted } from '@/shared/animations'
import SkeletonCard from '@/shared/components/patterns/SkeletonCard.vue'

export interface StatsCardProps {
  label: string
  value?: number
  prefix?: string
  suffix?: string
  desc?: string
  /** sage | gray | rose | pale | deep | cream | dust（奶油低饱和填充，tokens.css --app-stat-*） */
  color?: string
  path?: string
  loading?: boolean
  /** 右上角呼吸点（如「运行中任务」） */
  live?: boolean
  /** 趋势百分比（正负），与 trendLabel 一起显示在数值下方 */
  trend?: number
  trendLabel?: string
}

const props = withDefaults(defineProps<StatsCardProps>(), {
  value: 0,
  prefix: '',
  suffix: '',
  desc: '',
  color: 'sage',
  path: '',
  loading: false,
  live: false,
  trend: undefined,
  trendLabel: '',
})

const router = useRouter()
const valueRef = ref<HTMLElement | null>(null)
const displayed = ref(false)

// ── 奶油低饱和填充映射（tokens.css ── 仪表盘统计卡 ──） ──
const STAT_FILLS: Record<string, string> = {
  sage: 'var(--app-stat-sage)',
  gray: 'var(--app-stat-gray)',
  rose: 'var(--app-stat-rose)',
  pale: 'var(--app-stat-pale)',
  deep: 'var(--app-stat-deep)',
  cream: 'var(--app-stat-cream)',
  dust: 'var(--app-stat-dust)',
}

const fill = computed(() => STAT_FILLS[props.color] || STAT_FILLS['sage'])

const trendText = computed(() => {
  if (props.trend === undefined) return ''
  if (props.trend === 0) return props.trendLabel || '0%'
  const arrow = props.trend > 0 ? '↑' : '↓'
  return `${arrow}${Math.abs(props.trend)}% ${props.trendLabel}`.trim()
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
    :class="{ 'is-clickable': !!path }"
    :style="{ '--fill': fill }"
    :role="path ? 'button' : undefined"
    :tabindex="path ? 0 : undefined"
    @mouseenter="onCardEnter"
    @click="navigate"
    @keydown.enter.prevent="navigate"
    @keydown.space.prevent="navigate"
  >
    <SkeletonCard v-if="loading" />

    <template v-else>
      <!-- 彩色铅笔排线填充带：图标 + 标签同行，居中，位于填充区内 -->
      <div class="stats-card__band">
        <span class="stats-card__icon-chip">
          <slot name="icon">
            <div class="stats-card__icon-placeholder"></div>
          </slot>
        </span>
        <div class="stats-card__title">{{ label }}</div>
        <span v-if="live" class="stats-card__live" aria-hidden="true"></span>
      </div>

      <!-- 数值区：居中 -->
      <div class="stats-card__stat">
        <strong ref="valueRef">{{ prefix }}{{ value.toLocaleString() }}{{ suffix }}</strong>
        <small v-if="trendText">{{ trendText }}</small>
        <div class="stats-card__desc">{{ desc || '核心指标实时更新' }}</div>
      </div>

      <button
        v-if="path"
        type="button"
        class="stats-card__enter"
        @click.stop="navigate"
      >
        进入
      </button>
    </template>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════
   统计卡 — 铅笔涂鸦 × 奶油低饱和（方角十字收角）
   ═══════════════════════════════════════════ */
.stats-card {
  position: relative;
  background: var(--app-bg-card, #fff);
  border: 2.5px solid var(--app-stat-line);
  border-radius: 0; /* 方角设计 */
  box-shadow: 3px 3px 0 var(--app-stat-shadow);
  display: flex;
  flex-direction: column;
  aspect-ratio: 1 / 1; /* 方形 */
  transition: transform var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
}
.stats-card:hover {
  transform: translate(-1px, -1px);
  box-shadow: 5px 5px 0 var(--app-stat-shadow-hover);
}
.stats-card:focus-visible {
  outline: 2px dashed var(--app-stat-line);
  outline-offset: 4px;
}
.stats-card.is-clickable { cursor: pointer; }

/* 四角十字交叉笔触 */
.stats-card::before {
  content: '';
  position: absolute;
  inset: -3px;
  pointer-events: none;
  z-index: 3;
  background:
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) left 0 top 0 / 14px 2.5px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) left 0 top 0 / 2.5px 14px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) right 0 top 0 / 14px 2.5px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) right 0 top 0 / 2.5px 14px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) left 0 bottom 0 / 14px 2.5px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) left 0 bottom 0 / 2.5px 14px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) right 0 bottom 0 / 14px 2.5px no-repeat,
    linear-gradient(var(--app-stat-line), var(--app-stat-line)) right 0 bottom 0 / 2.5px 14px no-repeat;
}

/* 奶油低饱和铅笔排线填充带：边缘留白内嵌，直线描边 */
.stats-card__band {
  position: relative;
  height: 36px;
  flex-shrink: 0;
  margin: 6px 6px 0; /* 边缘留白：填充区与卡片边框的间隙 */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 6px;
  border: 2px solid var(--app-stat-line);
  background:
    repeating-linear-gradient(115deg, rgba(122,120,116,0.10) 0 1.5px, transparent 1.5px 7px),
    repeating-linear-gradient(65deg, rgba(255,255,255,0.55) 0 1.5px, transparent 1.5px 9px),
    var(--fill);
}
.stats-card__icon-chip {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.85);
  border: 1.5px solid var(--app-stat-line);
  color: var(--app-stat-line);
}
.stats-card__icon-chip :deep(svg) {
  stroke: var(--app-stat-line);
  color: var(--app-stat-line);
}
.stats-card__icon-placeholder {
  width: 12px;
  height: 12px;
  background: var(--app-stat-line-soft);
}
.stats-card__title {
  font-size: var(--app-size-xs);
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--app-stat-text);
  white-space: nowrap;
}
.stats-card__live {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 8px;
  height: 8px;
  background: var(--app-bg-card, #fff);
  border: 2px solid var(--app-live);
  animation: livePulse 1.5s ease-in-out infinite;
}
@keyframes livePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.45); }
  50% { box-shadow: 0 0 0 6px rgba(248, 113, 113, 0); }
}

/* 数值区：居中 */
.stats-card__stat {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 6px 10px 0;
}
.stats-card__stat strong {
  display: block;
  font-family: var(--app-font-display);
  font-size: var(--app-size-2xl);
  font-weight: 800;
  color: var(--app-stat-text);
  line-height: 1;
}
.stats-card__stat small {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-stat-line-soft);
}
.stats-card__desc {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-stat-line-soft);
  text-align: center;
  line-height: 1.4;
}

.stats-card__enter {
  align-self: center;
  margin-bottom: 10px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--app-stat-text);
  background: var(--app-bg-card, #fff);
  border: 1.5px solid var(--app-stat-line);
  border-radius: 0;
  padding: 3px 8px;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.2;
}
.stats-card__enter:hover { background: var(--app-stat-hover); }

@media (prefers-reduced-motion: reduce) {
  .stats-card { transition: none; }
  .stats-card:hover { transform: none; }
}
</style>
