<script setup lang="ts">
/**
 * StatsCard — 仪表盘统计入口（薄包装共享 KpiCard entry）
 * 保留 count-up / loading / path 路由 / live / trend；视觉壳交给 KpiCard。
 */
import { ref, computed, watch } from "vue"
import { useRouter } from "vue-router"
import { countUpFormatted } from "@/shared/animations"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import KpiCard from "@/shared/components/KpiCard.vue"

export interface StatsCardProps {
  label: string
  value?: number
  prefix?: string
  suffix?: string
  desc?: string
  /** sage | gray | rose | pale | deep | cream | dust */
  color?: string
  path?: string
  loading?: boolean
  decimals?: number
  live?: boolean
  trend?: number
  trendLabel?: string
  deco?: "none" | "pin" | "tape"
  tilt?: number
  /** entry：是否显示「进入」；有 path 时整卡仍可点 */
  showEnter?: boolean
}

const props = withDefaults(defineProps<StatsCardProps>(), {
  value: 0,
  prefix: "",
  suffix: "",
  desc: "",
  color: "sage",
  path: "",
  loading: false,
  decimals: 0,
  live: false,
  trend: undefined,
  trendLabel: "",
  deco: "pin",
  tilt: undefined,
  showEnter: true,
})

const router = useRouter()
const valueRef = ref<HTMLElement | null>(null)
const displayed = ref(false)

const COLOR_ACCENTS: Record<string, string> = {
  sage: "var(--c-device)",
  gray: "var(--c-ai)",
  rose: "var(--c-runner)",
  pale: "var(--c-workflow)",
  deep: "var(--c-case)",
  cream: "var(--c-element)",
  dust: "var(--c-report)",
}

const fill = computed(() => COLOR_ACCENTS[props.color] || COLOR_ACCENTS.sage)

const descText = computed(() => props.desc || "核心指标实时更新")

const trendText = computed(() => {
  if (props.trend === undefined) return ""
  if (props.trend === 0) return props.trendLabel || "0%"
  const arrow = props.trend > 0 ? "↑" : "↓"
  return `${arrow}${Math.abs(props.trend)}% ${props.trendLabel}`.trim()
})

function displayValue(): string {
  return props.value.toLocaleString(undefined, {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  })
}

watch(
  () => props.value,
  (newVal) => {
    if (valueRef.value && displayed.value) {
      countUpFormatted(valueRef.value, 0, newVal, 800, props.prefix, props.suffix, props.decimals)
    }
  },
)

function onCardEnter() {
  if (!displayed.value) {
    displayed.value = true
    setTimeout(() => {
      if (valueRef.value) {
        countUpFormatted(
          valueRef.value,
          0,
          props.value,
          1200,
          props.prefix,
          props.suffix,
          props.decimals,
        )
      }
    }, 200)
  }
}

function navigate() {
  if (props.path) router.push(props.path)
}
</script>

<template>
  <div class="stats-card" @mouseenter="onCardEnter">
    <SkeletonCard v-if="loading" />

    <KpiCard
      v-else
      class="stats-card__shell"
      variant="entry"
      :label="label"
      :color="fill"
      :desc="descText"
      :live="live"
      :deco="deco"
      :tilt="tilt"
      :clickable="!!path"
      :enter-label="showEnter ? '进入' : ''"
      @click="navigate"
    >
      <template #icon>
        <slot name="icon">
          <div class="stats-card__icon-placeholder" />
        </slot>
      </template>

      <template #value>
        <div class="stats-card__stat">
          <strong ref="valueRef">{{ prefix }}{{ displayValue() }}{{ suffix }}</strong>
          <small v-if="trendText">{{ trendText }}</small>
        </div>
      </template>
    </KpiCard>
  </div>
</template>

<style scoped>
.stats-card {
  /* 趋势文字兜底色：全局 --app-status-success-text 缺省时的后备（tokens.css 无同值令牌）*/
  --stats-card-trend-text: var(--color-teal-29) /* -> --color-teal-29 */;
  width: 100%;
  min-width: 0;
}

.stats-card__shell {
  width: 100%;
}

.stats-card__icon-placeholder {
  width: 10px;
  height: 10px;
  background: var(--ink);
  opacity: 0.35;
}

.stats-card__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stats-card__stat strong {
  display: block;
  font-family: var(--app-font-display, var(--app-font, inherit));
  font-size: var(--app-size-2xl, 28px);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
}

.stats-card__stat small {
  font-size: var(--app-size-xs, 11px);
  font-weight: 700;
  color: var(--app-status-success-text, var(--stats-card-trend-text));
}
</style>
