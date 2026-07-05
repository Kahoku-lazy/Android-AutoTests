<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { animate } from 'animejs'

const props = defineProps({
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#a2d2ff' },
  height: { type: Number, default: 60 },
  label: { type: String, default: '' },
  animate: { type: Boolean, default: true },
})

const svgRef = ref(null)
const pathRef = ref(null)

const w = 200
const h = props.height
const pad = 2

function buildPath(values) {
  if (!values.length) return ''
  const max = Math.max(...values) || 1
  const min = Math.min(...values) || 0
  const range = max - min || 1
  const stepX = (w - pad * 2) / (values.length - 1 || 1)

  return values.map((v, i) => {
    const x = pad + i * stepX
    const y = h - pad - ((v - min) / range) * (h - pad * 2)
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')
}

function buildArea(values) {
  if (!values.length) return ''
  const line = buildPath(values)
  return `${line} L ${w - pad} ${h - pad} L ${pad} ${h - pad} Z`
}

onMounted(() => {
  if (props.animate && pathRef.value && props.data.length > 0) {
    const length = pathRef.value.getTotalLength()
    pathRef.value.style.strokeDasharray = length
    pathRef.value.style.strokeDashoffset = length
    animate(pathRef.value, {
      strokeDashoffset: [length, 0],
      duration: 1400,
      ease: 'inOutSine',
    })
  }
})

watch(() => props.data, () => {
  if (props.animate && pathRef.value && props.data.length > 0) {
    const length = pathRef.value.getTotalLength()
    pathRef.value.style.strokeDasharray = length
    pathRef.value.style.strokeDashoffset = length
    animate(pathRef.value, {
      strokeDashoffset: [length, 0],
      duration: 1000,
      ease: 'inOutSine',
    })
  }
})
</script>

<template>
  <div class="mini-chart">
    <span v-if="label" class="mini-chart__label">{{ label }}</span>
    <svg
      ref="svgRef"
      :viewBox="`0 0 ${w} ${h}`"
      :style="{ height: h + 'px', width: '100%' }"
      class="mini-chart__svg"
    >
      <!-- Area fill -->
      <path
        v-if="data.length > 0"
        :d="buildArea(data)"
        :fill="color + '20'"
        class="mini-chart__area"
      />
      <!-- Line -->
      <path
        v-if="data.length > 0"
        ref="pathRef"
        :d="buildPath(data)"
        :stroke="color"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
        class="mini-chart__line"
      />
      <!-- Last point dot -->
      <circle
        v-if="data.length > 0"
        :cx="w - pad - 4"
        :cy="h - pad - ((data[data.length-1] - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1)) * (h - pad * 2)"
        r="3"
        :fill="color"
        class="mini-chart__dot"
      />
    </svg>
  </div>
</template>

<style scoped>
.mini-chart {
  width: 100%;
}

.mini-chart__label {
  display: block;
  font-size: 11px;
  color: var(--text-secondary, #9a8c98);
  margin-bottom: 6px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.mini-chart__svg {
  display: block;
  overflow: visible;
}

.mini-chart__area {
  transition: fill 0.3s ease;
}

.mini-chart__dot {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.mini-chart__svg:hover .mini-chart__dot {
  opacity: 1;
}
</style>
