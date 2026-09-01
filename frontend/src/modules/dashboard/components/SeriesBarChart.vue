<script setup lang="ts">
import { useECharts } from '@/shared/composables/useECharts'

export interface SeriesBarSeries {
  name: string
  data: number[]
  color: string
}

const props = withDefaults(
  defineProps<{
    labels: string[]
    series: SeriesBarSeries[]
  }>(),
  {
    labels: () => [],
    series: () => [],
  },
)

// ⚠️ ECharts 渲染在 Canvas 上，不支持 CSS 变量，此处保留色值字面量。
//    token 对照：#1e1e24=--ink · #e8ecf1=--app-border-light · #f0ede8=--app-border-lighter
//    #999=--app-ink-muted；系列色由调用方按 token 同值传入。
function compactNumber(v: number): string {
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (v >= 1_000) return (v / 1_000).toFixed(1).replace(/\.0$/, '') + 'K'
  return String(v)
}

function buildOption() {
  return {
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    animationDurationUpdate: 450,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontSize: 12, color: '#1e1e24' },
      valueFormatter: compactNumber,
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 20,
      textStyle: { fontSize: 12, color: '#1e1e24', fontWeight: 700 },
    },
    grid: { top: 16, right: 8, bottom: 36, left: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: props.labels || [],
      axisLine: { lineStyle: { color: '#e8ecf1' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 12, color: '#999', fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f0ede8' } },
      axisLabel: { fontSize: 12, color: '#999', formatter: compactNumber },
    },
    series: (props.series || []).map((it, i) => ({
      name: it.name,
      type: 'bar',
      data: it.data || [],
      color: it.color,
      barMaxWidth: 16,
      itemStyle: { borderRadius: [4, 4, 0, 0] },
      animationDelay: (idx: number) => idx * 40 + i * 60,
    })),
    animationDelayUpdate: (idx: number) => idx * 30,
  }
}

const { container } = useECharts(buildOption, () => [props.labels, props.series])
</script>

<template>
  <div ref="container" class="series-bar-chart"></div>
</template>

<style scoped>
.series-bar-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
}
</style>
