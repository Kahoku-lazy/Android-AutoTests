<script setup lang="ts">
import { computed } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import type { ExecutionChart } from '@/shared/types/dashboard'

const props = withDefaults(defineProps<{ chart: ExecutionChart }>(), {
  chart: () => ({ labels: [], success: [], failed: [] }),
})

// ⚠️ ECharts 渲染在 Canvas 上，不支持 CSS 变量，此处保留色值字面量。
//    如需改色，修改此函数内的常量；CSS 文件使用 tokens.css 对应变量。
function buildOption() {
  const c = props.chart
  return {
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    animationDurationUpdate: 450,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontSize: 12 },
    },
    legend: {
      bottom: 0,
      itemWidth: 10, itemHeight: 10, itemGap: 20,
      textStyle: { fontSize: 11, color: '#1e1e24', fontWeight: 700 },
    },
    grid: { top: 12, right: 8, bottom: 36, left: 8 },
    xAxis: {
      type: 'category',
      data: c.labels || [],
      axisLine: { lineStyle: { color: '#e8ecf1' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#999', fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f0ede8' } },
      axisLabel: { fontSize: 10, color: '#999' },
    },
    series: [
      { name: '执行成功', type: 'bar', data: c.success || [], color: '#6BCB77',
        barMaxWidth: 14, itemStyle: { borderRadius: [2, 2, 0, 0] },
        animationDelay: (idx) => idx * 40 },
      { name: '执行失败', type: 'bar', data: c.failed || [], color: '#FFB5A7',
        barMaxWidth: 14, itemStyle: { borderRadius: [2, 2, 0, 0] },
        animationDelay: (idx) => idx * 40 + 60 },
    ],
    animationDelayUpdate: (idx) => idx * 30,
  }
}

const { container } = useECharts(buildOption, () => props.chart)
</script>

<template>
  <div ref="container" class="trend-bar-chart"></div>
</template>

<style scoped>
.trend-bar-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
}
</style>
