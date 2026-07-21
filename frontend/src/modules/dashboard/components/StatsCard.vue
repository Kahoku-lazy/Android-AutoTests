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
.stats-card {
  background: var(--app-glass-card, rgba(255, 255, 255, 0.65));
  backdrop-filter: blur(var(--app-glass-blur, 20px));
  -webkit-backdrop-filter: blur(var(--app-glass-blur, 20px));
  border-radius: var(--app-radius-md, 20px);
  padding: 20px 22px 18px;
  border: 1px solid var(--app-glass-border, rgba(255, 255, 255, 0.85));
  box-shadow: var(--app-shadow-sm, 0 4px 15px rgba(0, 0, 0, 0.02));
  transition: box-shadow 0.3s, transform 0.3s;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 168px;
}

.stats-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 20px 20px 0 0;
}

.stats-card.is-clickable {
  cursor: pointer;
}

.stats-card:hover {
  box-shadow: var(--app-shadow-md, 0 8px 25px rgba(0, 0, 0, 0.05));
  transform: translateY(-3px);
}

.stats-card--green::before { background: #95D5B2; }
.stats-card--blue::before { background: #BDE0FE; }
.stats-card--yellow::before { background: #F4D35E; }
.stats-card--pink::before { background: #FFB5A7; }
.stats-card--teal::before { background: #89CFF0; }
.stats-card--purple::before { background: #C9B6F2; }
.stats-card--orange::before { background: #5EEAD4; }

.stats-card__icon {
  width: 44px;
  height: 44px;
  border-radius: var(--app-radius-sm, 16px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: 14px;
  position: relative;
  box-shadow: var(--app-icon-shadow, 0 10px 24px rgba(74, 78, 105, 0.12));
}

.stats-card__icon :deep(svg) {
  width: 22px;
  height: 22px;
  color: #fff;
  stroke: #fff;
}

.stats-card__icon-placeholder {
  width: 18px;
  height: 18px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.45);
}

.stats-card__title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--app-text, #4a4e69);
  margin-bottom: 4px;
  line-height: 1.3;
}

.stats-card__desc {
  font-size: 0.78rem;
  color: var(--app-text-secondary, #9a8c98);
  line-height: 1.45;
  margin-bottom: 14px;
  flex: 1;
}

.stats-card__footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
}

.stats-card__stat {
  min-width: 0;
}

.stats-card__stat strong {
  display: block;
  font-family: var(--app-font-display, Quicksand, sans-serif);
  font-size: 1.55rem;
  font-weight: 800;
  color: var(--app-text, #4a4e69);
  letter-spacing: -0.4px;
  line-height: 1.15;
}

.stats-card__stat small {
  display: block;
  margin-top: 2px;
  font-size: 0.68rem;
  color: var(--app-text-secondary, #9a8c98);
  letter-spacing: 0.2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats-card__enter {
  flex-shrink: 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  padding: 6px 16px;
  border-radius: var(--app-radius-pill, 50px);
  border: none;
  cursor: pointer;
  transition: transform 0.2s, filter 0.2s;
  font-family: inherit;
  line-height: 1.2;
}

.stats-card__enter:hover {
  transform: translateY(-1px);
  filter: brightness(1.08);
}

/* Skeleton */
.stats-card__skeleton {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 2px 0;
}

.skeleton-bar {
  background: linear-gradient(
    90deg,
    rgba(137, 207, 240, 0.06) 25%,
    rgba(137, 207, 240, 0.14) 50%,
    rgba(137, 207, 240, 0.06) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
  border-radius: 8px;
}

.skeleton-bar--icon { width: 44px; height: 44px; border-radius: 14px; }
.skeleton-bar--value { width: 55%; height: 22px; }
.skeleton-bar--label { width: 80%; height: 14px; }
.skeleton-bar--footer { width: 100%; height: 28px; margin-top: 4px; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .stats-card,
  .stats-card__enter {
    transition: none;
  }
  .stats-card:hover {
    transform: none;
  }
  .skeleton-bar {
    animation: none;
  }
}
</style>
