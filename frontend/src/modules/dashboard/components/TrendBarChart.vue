<script setup>
import { computed } from 'vue'

const props = defineProps({
  chart: {
    type: Object,
    default: () => ({ labels: [], success: [], failed: [], new_cases: [] }),
  },
  height: { type: Number, default: 160 },
})

const series = [
  { key: 'success', label: '执行成功', color: '#6fba2c' },
  { key: 'failed', label: '执行失败', color: '#e05a5a' },
  { key: 'new_cases', label: '新建用例', color: '#889df0' },
]

const w = 640
const pad = { top: 12, right: 8, bottom: 28, left: 8 }

const maxVal = computed(() => {
  const vals = [
    ...(props.chart.success || []),
    ...(props.chart.failed || []),
    ...(props.chart.new_cases || []),
  ]
  return Math.max(...vals, 1)
})

const labels = computed(() => props.chart.labels || [])
const count = computed(() => labels.value.length || 1)

const groupWidth = computed(() => (w - pad.left - pad.right) / count.value)
const barWidth = computed(() => Math.min(14, groupWidth.value / 4))

function barHeight(val) {
  const innerH = props.height - pad.top - pad.bottom
  return (val / maxVal.value) * innerH
}

function barX(groupIndex, seriesIndex) {
  const gx = pad.left + groupIndex * groupWidth.value + groupWidth.value / 2
  const offset = (seriesIndex - 1) * (barWidth.value + 3)
  return gx + offset - barWidth.value / 2
}

function barY(val) {
  return props.height - pad.bottom - barHeight(val)
}
</script>

<template>
  <div class="trend-bar-chart">
    <div class="trend-bar-chart__legend">
      <span v-for="s in series" :key="s.key" class="legend-item">
        <i class="legend-dot" :style="{ background: s.color }"></i>{{ s.label }}
      </span>
    </div>
    <svg
      :viewBox="`0 0 ${w} ${height}`"
      class="trend-bar-chart__svg"
      preserveAspectRatio="xMidYMid meet"
    >
      <line
        :x1="pad.left" :y1="height - pad.bottom"
        :x2="w - pad.right" :y2="height - pad.bottom"
        stroke="rgba(121, 79, 39, 0.15)" stroke-width="1"
      />
      <g v-for="(label, gi) in labels" :key="label + gi">
        <g v-for="(s, si) in series" :key="s.key">
          <rect
            :x="barX(gi, si)"
            :y="barY(chart[s.key]?.[gi] || 0)"
            :width="barWidth"
            :height="barHeight(chart[s.key]?.[gi] || 0)"
            :fill="s.color"
            rx="3"
            class="bar-rect"
          >
            <title>{{ s.label }}: {{ chart[s.key]?.[gi] || 0 }}</title>
          </rect>
        </g>
        <text
          :x="pad.left + gi * groupWidth + groupWidth / 2"
          :y="height - 8"
          text-anchor="middle"
          class="bar-label"
        >{{ label }}</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.trend-bar-chart {
  width: 100%;
}

.trend-bar-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 10px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #725d42;
  font-weight: 600;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
}

.trend-bar-chart__svg {
  width: 100%;
  height: auto;
  display: block;
}

.bar-label {
  font-size: 10px;
  fill: #9f927d;
  font-weight: 600;
}

.bar-rect {
  transition: opacity 0.2s ease;
}

.bar-rect:hover {
  opacity: 0.85;
}
</style>
