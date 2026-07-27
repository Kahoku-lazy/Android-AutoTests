<template>
  <div class="rate-bar">
    <div class="rate-bar__track">
      <div class="rate-bar__pass" :style="{ width: rate + '%' }" />
      <div v-if="showFail && failRate > 0" class="rate-bar__fail" :style="{ width: failRate + '%' }" />
    </div>
    <span v-if="showLabel" class="rate-bar__label" :class="rateClass">{{ rate }}%</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 通过率 0-100 */
  rate: { type: Number, required: true },
  /** 是否显示失败段 */
  showFail: { type: Boolean, default: true },
  /** 是否显示百分比文字 */
  showLabel: { type: Boolean, default: true },
})

const failRate = computed(() => Math.max(0, 100 - props.rate))

const rateClass = computed(() => {
  if (props.rate >= 95) return 'rate-bar__label--ok'
  if (props.rate >= 80) return 'rate-bar__label--warn'
  return 'rate-bar__label--bad'
})
</script>

<style scoped>
.rate-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.rate-bar__track {
  height: 8px;
  background: #f0ede8;
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid var(--ink);
  flex: 1;
  min-width: 60px;
  display: flex;
}

.rate-bar__pass {
  height: 100%;
  background: var(--c-device, #6BCB77);
  border-radius: 2px;
  transition: width 0.3s var(--app-ease);
}

.rate-bar__fail {
  height: 100%;
  background: var(--c-runner, #FFB5A7);
  transition: width 0.3s var(--app-ease);
}

.rate-bar__label {
  font-size: var(--app-size-xs);
  font-weight: 700;
  min-width: 36px;
  text-align: right;
}

.rate-bar__label--ok {
  color: #2d7a2d;
}

.rate-bar__label--warn {
  color: #b08800;
}

.rate-bar__label--bad {
  color: #a03030;
}
</style>
