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
  /** sage | gray | rose | pale | deep | cream | dust（奶油低饱和点缀，tokens.css --app-stat-*） */
  color?: string
  path?: string
  loading?: boolean
  /** 数值小数位（如 1.23M 传 2、2.5K 传 1） */
  decimals?: number
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
  decimals: 0,
  live: false,
  trend: undefined,
  trendLabel: '',
})

const router = useRouter()
const valueRef = ref<HTMLElement | null>(null)
const displayed = ref(false)

// ── 饱和度强调色映射（模块色 token，用于顶部条 / 图标 chip 底 / 图标描边） ──
const COLOR_ACCENTS: Record<string, string> = {
  sage:  'var(--c-device)',    // 设备在线 — 薄荷绿
  gray:  'var(--c-ai)',        // 活跃智能体 — 柔粉
  rose:  'var(--c-runner)',    // 运行中任务 — 桃粉
  pale:  'var(--c-workflow)',  // 工作流 — 天蓝
  deep:  'var(--c-case)',      // Android 用例/元素 — 青绿
  cream: 'var(--c-element)',   // API 用例/接口 — 薰衣草紫
  dust:  'var(--c-report)',    // 功能业务 — 灰紫
}

const fill = computed(() => COLOR_ACCENTS[props.color] || COLOR_ACCENTS['sage'])

const trendText = computed(() => {
  if (props.trend === undefined) return ''
  if (props.trend === 0) return props.trendLabel || '0%'
  const arrow = props.trend > 0 ? '↑' : '↓'
  return `${arrow}${Math.abs(props.trend)}% ${props.trendLabel}`.trim()
})

function displayValue(): string {
  return props.value.toLocaleString(undefined, {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  })
}

watch(() => props.value, (newVal) => {
  if (valueRef.value && displayed.value) {
    countUpFormatted(valueRef.value, 0, newVal, 800, props.prefix, props.suffix, props.decimals)
  }
})

function onCardEnter() {
  if (!displayed.value) {
    displayed.value = true
    setTimeout(() => {
      if (valueRef.value) {
        countUpFormatted(valueRef.value, 0, props.value, 1200, props.prefix, props.suffix, props.decimals)
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
    :style="{ '--accent': fill }"
    :role="path ? 'button' : undefined"
    :tabindex="path ? 0 : undefined"
    @mouseenter="onCardEnter"
    @click="navigate"
    @keydown.enter.prevent="navigate"
    @keydown.space.prevent="navigate"
  >
    <SkeletonCard v-if="loading" />

    <template v-else>
      <!-- 头部：模块色图标 + 标签同行，右上角 live 呼吸点 -->
      <div class="stats-card__head">
        <span class="stats-card__icon-chip">
          <slot name="icon">
            <div class="stats-card__icon-placeholder"></div>
          </slot>
        </span>
        <span class="stats-card__title">{{ label }}</span>
        <span v-if="live" class="stats-card__live" aria-hidden="true"></span>
      </div>

      <!-- 数值区：居中 -->
      <div class="stats-card__stat">
        <strong ref="valueRef">{{ prefix }}{{ displayValue() }}{{ suffix }}</strong>
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
   统计卡 — 纯净指标卡（白底 · 模块色点缀 · 统一圆角轻阴影）
   ═══════════════════════════════════════════ */
.stats-card {
  position: relative;
  background: var(--app-bg-card, #fff);
  border: 1px solid var(--app-border-light);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-sm);
  display: flex;
  flex-direction: column;
  min-height: 116px;
  transition: transform var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease),
    border-color var(--app-duration) var(--app-ease);
}
.stats-card::before {
  /* 顶部模块色点缀条 */
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: var(--app-radius-md) var(--app-radius-md) 0 0;
  background: var(--accent);
  pointer-events: none;
}
.stats-card:hover {
  transform: translate(-1px, -1px);
  box-shadow: var(--app-shadow-lg);
  border-color: var(--app-border-lighter);
}
.stats-card:focus-visible {
  outline: 2px solid var(--app-status-purple);
  outline-offset: 3px;
}
.stats-card.is-clickable { cursor: pointer; }

/* 头部：图标 + 标签 */
.stats-card__head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 12px 0;
  flex-shrink: 0;
  min-width: 0;
}
.stats-card__icon-chip {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: var(--accent);
  color: #fff;
}
.stats-card__icon-chip :deep(svg) {
  stroke: #fff;
  color: #fff;
}
.stats-card__icon-placeholder {
  width: 12px;
  height: 12px;
  background: var(--accent);
}
.stats-card__title {
  flex: 1;
  min-width: 0;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  line-height: 1.3;
}
.stats-card__live {
  position: absolute;
  top: 8px;
  right: 9px;
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
  gap: var(--app-space-xs);
  padding: 0 14px;
}
.stats-card__stat strong {
  display: block;
  font-family: var(--app-font-display);
  font-size: var(--app-size-2xl);
  font-weight: 800;
  /* 用主题偏移色加深，保证白卡上的对比度与"数值=主题色"辨识 */
  color: color-mix(in srgb, var(--accent) 62%, var(--ink));
  line-height: 1.15;
}
.stats-card__stat small {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-status-success-text);
}
.stats-card__desc {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-ink-muted);
  text-align: center;
  line-height: 1.4;
}

.stats-card__enter {
  align-self: center;
  margin: var(--app-space-sm) 0 14px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--ink);
  background: var(--app-bg-subtle);
  border: 1px solid var(--app-border-light);
  border-radius: 999px;
  padding: var(--app-space-xs) 12px;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.2;
  transition: background var(--app-duration-fast) var(--app-ease),
    border-color var(--app-duration-fast) var(--app-ease),
    color var(--app-duration-fast) var(--app-ease);
}
.stats-card__enter:hover {
  background: var(--app-highlight);
  border-color: var(--app-highlight);
  color: var(--ink);
}

@media (prefers-reduced-motion: reduce) {
  .stats-card { transition: none; }
  .stats-card:hover { transform: none; }
  .stats-card__live { animation: none; }
}
</style>
