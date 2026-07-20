<script setup>
import { ref, onMounted, watch } from 'vue'
import { countUpFormatted, elasticHover } from '@/shared/animations.js'
// AppCard → el-card (Element Plus auto-import)

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  trend: { type: Number, default: 0 },
  trendLabel: { type: String, default: '' },
  color: { type: String, default: 'app-teal' },
  pattern: { type: String, default: 'app-teal' },
  loading: { type: Boolean, default: false },
})

const cardRef = ref(null)
const valueRef = ref(null)
const displayed = ref(false)

onMounted(() => {
  if (cardRef.value) {
    elasticHover(cardRef.value.$el || cardRef.value)
  }
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
</script>

<template>
  <el-card
    ref="cardRef"
    class="stats-card"
    @mouseenter="onCardEnter"
  >
    <!-- Skeleton loader -->
    <div v-if="loading" class="stats-card__skeleton">
      <div class="skeleton-bar skeleton-bar--icon"></div>
      <div class="skeleton-bar skeleton-bar--value"></div>
      <div class="skeleton-bar skeleton-bar--label"></div>
    </div>

    <template v-else>
      <div class="stats-card__inner">
        <!-- Icon area -->
        <div class="stats-card__icon-wrap soft-icon soft-icon--blue">
          <slot name="icon">
            <div class="stats-card__icon-placeholder"></div>
          </slot>
        </div>

        <!-- Value -->
        <div class="stats-card__body">
          <div ref="valueRef" class="stats-card__value">
            {{ prefix }}{{ value.toLocaleString() }}{{ suffix }}
          </div>
          <div class="stats-card__label">{{ label }}</div>
        </div>

        <!-- Trend -->
        <div v-if="trend !== 0" class="stats-card__trend" :class="trend > 0 ? 'is-up' : 'is-down'">
          <span class="stats-card__trend-arrow">{{ trend > 0 ? '&#8593;' : '&#8595;' }}</span>
          <span>{{ Math.abs(trend) }}%</span>
          <span v-if="trendLabel" class="stats-card__trend-label">{{ trendLabel }}</span>
        </div>
      </div>
    </template>
  </el-card>
</template>

<style scoped>
.stats-card {
  cursor: default;
}

.stats-card :deep(.el-card__body) {
  padding: 20px 22px;
}

.stats-card__inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-card__icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
}

.stats-card__icon-wrap :deep(svg) {
  width: 22px;
  height: 22px;
}

.stats-card__icon-placeholder {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: var(--app-green-deep);
  opacity: 0.25;
}

.stats-card__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stats-card__value {
  font-family: var(--font-display, Nunito, sans-serif);
  font-size: 30px;
  font-weight: 800;
  color: var(--animal-text-color, #794f27);
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.stats-card__label {
  font-size: 13px;
  color: var(--app-text-secondary, #9f927d);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stats-card__trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  align-self: flex-start;
}

.stats-card__trend.is-up {
  background: rgba(111, 186, 44, 0.12);
  color: var(--app-green-deep, #6fba2c);
}

.stats-card__trend.is-down {
  background: rgba(224, 90, 90, 0.12);
  color: #e8998a;
}

.stats-card__trend-arrow {
  font-size: 14px;
}

.stats-card__trend-label {
  font-weight: 400;
  opacity: 0.8;
}

/* Skeleton */
.stats-card__skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 4px 0;
}

.skeleton-bar {
  background: linear-gradient(90deg, rgba(121,79,39,0.06) 25%, rgba(121,79,39,0.12) 50%, rgba(121,79,39,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
  border-radius: 8px;
}

.skeleton-bar--icon { width: 44px; height: 44px; border-radius: 14px; }
.skeleton-bar--value { width: 70%; height: 30px; }
.skeleton-bar--label { width: 40%; height: 14px; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
