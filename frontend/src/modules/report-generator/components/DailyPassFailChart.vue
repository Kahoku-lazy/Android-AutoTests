<script setup>
import { computed } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import { CHART_COLORS, CHART_VISIBLE_DAYS } from '../constants'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  pass: { type: Array, default: () => [] },
  fail: { type: Array, default: () => [] },
  visibleDays: { type: Number, default: CHART_VISIBLE_DAYS },
  group: { type: String, default: 'report-trend' },
})

const zoomStart = computed(() => {
  const n = props.labels.length
  if (n <= props.visibleDays) return 0
  return ((n - props.visibleDays) / n) * 100
})

function buildOption() {
  const passColor = CHART_COLORS.passBar
  const failColor = CHART_COLORS.failBar
  return {
    animation: true,
    animationDuration: 700,
    animationEasing: 'cubicOut',
    animationDurationUpdate: 400,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontSize: 12 },
    },
    legend: {
      bottom: 22, itemWidth: 10, itemHeight: 10, itemGap: 18,
      textStyle: { fontSize: 12, color: '#725d42', fontWeight: 600 },
    },
    grid: { top: 12, right: 12, bottom: 72, left: 36 },
    dataZoom: [
      {
        type: 'slider', start: zoomStart.value, end: 100,
        height: 16, bottom: 4,
        borderColor: 'rgba(121,79,39,0.15)',
        fillerColor: 'rgba(25,200,185,0.18)',
        handleStyle: { color: '#19c8b9' },
        textStyle: { fontSize: 10, color: '#9f927d' },
      },
      { type: 'inside', start: zoomStart.value, end: 100 },
    ],
    xAxis: {
      type: 'category', data: props.labels,
      axisLine: { lineStyle: { color: 'rgba(121,79,39,0.15)' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#9f927d', fontWeight: 600 },
    },
    yAxis: {
      type: 'value', minInterval: 1,
      axisLabel: { fontSize: 10, color: '#9f927d' },
      splitLine: { lineStyle: { color: 'rgba(121,79,39,0.08)' } },
    },
    series: [
      {
        name: '通过', type: 'bar', data: props.pass, barMaxWidth: 16,
        itemStyle: {
          color: passColor.fill, borderColor: passColor.stroke,
          borderWidth: 1.5, borderRadius: [6, 6, 0, 0],
        },
      },
      {
        name: '失败', type: 'bar', data: props.fail, barMaxWidth: 16,
        itemStyle: {
          color: failColor.fill, borderColor: failColor.stroke,
          borderWidth: 1.5, borderRadius: [6, 6, 0, 0],
        },
      },
    ],
  }
}

const { container } = useECharts(buildOption, () => [props.labels, props.pass, props.fail, props.visibleDays], { group: props.group })
</script>

<template>
  <div ref="container" class="echart-host" />
</template>

<style scoped>
.echart-host { width: 100%; height: 220px; }
</style>
