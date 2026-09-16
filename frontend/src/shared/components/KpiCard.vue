<script setup lang="ts">
/**
 * KpiCard — 共享统计卡（Hand-Drawn Doodle 壳）
 *
 * variant:
 * - kpi（默认）：紧凑指标（shape + label + value），兼容既有调用
 * - entry：仪表盘入口（图标 + 标题 + 数值 + 描述 + 进入）
 *
 * 视觉 DNA：虚线边 / 近直角 / 硬偏移色阴影 / 可选微倾与图钉胶带
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value?: string | number
    label?: string
    color?: string
    /** kpi 变体几何点缀 */
    shape?: 'diamond' | 'triangle' | 'square' | 'circle'
    variant?: 'kpi' | 'entry'
    /** entry：描述文案 */
    desc?: string
    /** entry：显示「进入」并允许整卡激活 */
    enterLabel?: string
    /** entry：live 指示点 */
    live?: boolean
    /** 装饰：无 / 图钉 / 胶带 */
    deco?: 'none' | 'pin' | 'tape'
    /** 微倾角度（deg）；不传则用 CSS 默认 */
    tilt?: number
    /** 是否可点击（kpi 默认可点；entry 在有 enterLabel 或显式 true 时可点） */
    clickable?: boolean
  }>(),
  {
    value: '',
    label: '',
    color: 'var(--c-dashboard)',
    shape: 'diamond',
    variant: 'kpi',
    desc: '',
    enterLabel: '进入',
    live: false,
    deco: 'none',
    tilt: undefined,
    clickable: undefined,
  },
)

const emit = defineEmits<{
  click: [e: MouseEvent | KeyboardEvent]
}>()

const isEntry = computed(() => props.variant === 'entry')

const isClickable = computed(() => {
  if (props.clickable !== undefined) return props.clickable
  return isEntry.value ? Boolean(props.enterLabel) : true
})

const rootStyle = computed(() => {
  const style: Record<string, string> = {
    '--kpi-accent': props.color,
  }
  if (props.tilt !== undefined) {
    style['--kpi-tilt'] = `${props.tilt}deg`
  }
  return style
})

function onActivate(e: MouseEvent | KeyboardEvent) {
  if (!isClickable.value) return
  emit('click', e)
}

function onKeydown(e: KeyboardEvent) {
  if (!isClickable.value) return
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    onActivate(e)
  }
}
</script>

<template>
  <div
    class="kpi-card"
    :class="[
      `kpi-card--${variant}`,
      { 'is-clickable': isClickable, 'has-deco': deco !== 'none' },
    ]"
    :style="rootStyle"
    :role="isClickable ? 'button' : undefined"
    :tabindex="isClickable ? 0 : undefined"
    @click="onActivate"
    @keydown="onKeydown"
  >
    <span v-if="deco === 'pin'" class="kpi-card__pin" aria-hidden="true" />
    <span v-if="deco === 'tape'" class="kpi-card__tape" aria-hidden="true" />

    <!-- ── kpi：紧凑指标 ── -->
    <template v-if="!isEntry">
      <div
        class="kpi-card__shape"
        :class="`kpi-card__shape--${shape}`"
        :style="{ background: color }"
      >
        <span v-if="shape !== 'circle'" class="kpi-card__shape-inner" />
      </div>
      <div class="kpi-card__label" :style="{ color }">{{ label }}</div>
      <div class="kpi-card__value">
        <slot name="value">{{ value }}</slot>
      </div>
      <slot />
    </template>

    <!-- ── entry：仪表盘入口 ── -->
    <template v-else>
      <div class="kpi-card__head">
        <span class="kpi-card__icon">
          <slot name="icon">
            <span class="kpi-card__icon-fallback" />
          </slot>
        </span>
        <span class="kpi-card__title">{{ label }}</span>
        <span v-if="live" class="kpi-card__live" aria-hidden="true" />
      </div>

      <div class="kpi-card__stat">
        <slot name="value">
          <strong class="kpi-card__value">{{ value }}</strong>
        </slot>
        <div v-if="desc || $slots.desc" class="kpi-card__desc">
          <slot name="desc">{{ desc }}</slot>
        </div>
      </div>

      <button
        v-if="enterLabel && isClickable"
        type="button"
        class="kpi-card__enter"
        @click.stop="onActivate"
      >
        {{ enterLabel }}
      </button>

      <slot />
    </template>
  </div>
</template>

<style scoped>
.kpi-card {
  --kpi-accent: var(--comp-kpi-accent);
  /* 图钉 / 胶带 / 图标硬阴影与形状描边（rgba 装饰绘制色登记处） */
  --kpi-pin-shadow: var(--comp-kpi-pin-shadow);
  --kpi-tape-border: var(--comp-kpi-tape-border);
  --kpi-icon-shadow: var(--comp-kpi-icon-shadow);
  --kpi-shape-border: var(--comp-kpi-shape-border);
  /* live 指示点脉冲（rgba 状态绘制色登记处） */
  --kpi-live-pulse: var(--comp-kpi-live-pulse);
  --kpi-live-pulse-fade: var(--comp-kpi-live-pulse-fade);
  --kpi-tilt: var(--comp-kpi-tilt);
  --kpi-radius: var(--comp-kpi-radius);
  position: relative;
  background: #fff;
  border: 2.5px dashed var(--ink);
  border-radius: var(--kpi-radius);
  box-shadow: 4px 4px 0 0 var(--kpi-accent);
  transform: rotate(var(--kpi-tilt));
  transition:
    transform var(--app-duration, 0.2s) var(--app-ease, ease),
    box-shadow var(--app-duration, 0.2s) var(--app-ease, ease);
}

.kpi-card.is-clickable {
  cursor: pointer;
}

.kpi-card.is-clickable:hover {
  transform: rotate(0deg) translate(-1px, -1px);
  box-shadow: 5px 5px 0 0 var(--kpi-accent);
}

.kpi-card:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 3px;
}

/* 装饰：不拦截点击 */
.kpi-card__pin,
.kpi-card__tape {
  position: absolute;
  z-index: 2;
  pointer-events: none;
}

.kpi-card__pin {
  top: -7px;
  left: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--ink);
  background: var(--kpi-accent);
  transform: translateX(-50%);
  box-shadow: 1px 2px 0 0 var(--kpi-pin-shadow);
}

.kpi-card__tape {
  top: -10px;
  left: 50%;
  width: 64px;
  height: 18px;
  transform: translateX(-50%) rotate(-2deg);
  opacity: 0.48;
  border: 1px solid var(--kpi-tape-border);
  background: repeating-linear-gradient(
    90deg,
    color-mix(in srgb, var(--kpi-accent) 70%, #fff),
    color-mix(in srgb, var(--kpi-accent) 70%, #fff) 8px,
    var(--kpi-accent) 8px,
    var(--kpi-accent) 16px
  );
}

/* ── kpi 变体 ── */
.kpi-card--kpi {
  text-align: center;
  padding: var(--app-space-md, 12px) var(--app-space-lg, 16px) var(--app-space-sm, 8px);
  min-width: 120px;
}

.kpi-card__shape {
  width: 22px;
  height: 22px;
  margin: 0 auto 10px;
  border: 2px solid var(--kpi-shape-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-card__shape-inner {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 1px;
}

.kpi-card__shape--diamond {
  transform: rotate(45deg);
}

.kpi-card__shape--triangle {
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  border: none;
  width: 24px;
  height: 20px;
}

.kpi-card__shape--triangle .kpi-card__shape-inner {
  width: 5px;
  height: 5px;
  margin-top: var(--app-space-xs, 4px);
}

.kpi-card__shape--square {
  border-radius: 2px;
}

.kpi-card__shape--circle {
  border-radius: 50%;
}

.kpi-card__shape--circle .kpi-card__shape-inner {
  display: none;
}

.kpi-card--kpi .kpi-card__label {
  font-size: var(--app-size-sm, 13px);
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}

.kpi-card--kpi .kpi-card__value {
  font-family: var(--app-font, inherit);
  font-size: var(--app-size-2xl, 28px);
  font-weight: 800;
  color: var(--ink);
  line-height: 1.1;
}

/* ── entry 变体 ── */
.kpi-card--entry {
  display: flex;
  flex-direction: column;
  min-height: 142px;
  width: 100%;
  padding: 14px 12px 10px;
}

.kpi-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  min-width: 0;
}

.kpi-card__icon {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border: 2px solid var(--ink);
  border-radius: var(--kpi-radius);
  background: var(--kpi-accent);
  color: var(--ink);
  box-shadow: 2px 2px 0 0 var(--kpi-icon-shadow);
}

.kpi-card__icon :deep(svg) {
  width: 14px;
  height: 14px;
  stroke: var(--ink);
  color: var(--ink);
}

.kpi-card__icon-fallback {
  width: 10px;
  height: 10px;
  background: var(--ink);
  opacity: 0.35;
}

.kpi-card__title {
  flex: 1;
  min-width: 0;
  font-size: var(--app-size-sm, 13px);
  font-weight: 800;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.kpi-card__live {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid var(--app-live);
  background: #fff;
  animation: kpiLivePulse 1.5s ease-in-out infinite;
}

@keyframes kpiLivePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--kpi-live-pulse);
  }
  50% {
    box-shadow: 0 0 0 5px var(--kpi-live-pulse-fade);
  }
}

.kpi-card__stat {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-align: center;
  padding: 0 4px;
}

.kpi-card--entry .kpi-card__value,
.kpi-card__stat :deep(strong) {
  display: block;
  font-family: var(--app-font-display, var(--app-font, inherit));
  font-size: var(--app-size-2xl, 28px);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--ink);
}

.kpi-card__stat :deep(small) {
  font-size: var(--app-size-xs, 11px);
  font-weight: 700;
  color: var(--app-status-success-text);
}

.kpi-card__desc {
  font-size: var(--app-size-xs, 11px);
  font-weight: 600;
  color: var(--app-text-secondary);
  line-height: 1.4;
}

.kpi-card__enter {
  align-self: center;
  margin-top: 8px;
  font-family: inherit;
  font-size: var(--app-size-xs, 11px);
  font-weight: 800;
  color: var(--ink);
  background: var(--c-dashboard);
  border: 2px solid var(--ink);
  border-radius: var(--kpi-radius);
  padding: 3px 12px;
  box-shadow: 2px 2px 0 0 var(--c-workflow);
  cursor: pointer;
  line-height: 1.2;
}

.kpi-card__enter:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--c-workflow);
}

@media (prefers-reduced-motion: reduce) {
  .kpi-card {
    transform: none;
    transition: none;
  }
  .kpi-card.is-clickable:hover {
    transform: none;
  }
  .kpi-card__live {
    animation: none;
  }
  .kpi-card__enter:hover {
    transform: none;
  }
}
</style>
