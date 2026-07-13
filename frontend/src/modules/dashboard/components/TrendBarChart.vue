<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chart: {
    type: Object,
    default: () => ({ labels: [], success: [], failed: [], new_cases: [] }),
  },
})

const container = ref(null)
let instance = null
let resizeObserver = null

function buildOption() {
  const c = props.chart
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontSize: 12 },
    },
    legend: {
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 20,
      textStyle: { fontSize: 12, color: '#725d42', fontWeight: 600 },
    },
    grid: { top: 12, right: 8, bottom: 36, left: 8 },
    xAxis: {
      type: 'category',
      data: c.labels || [],
      axisLine: { lineStyle: { color: 'rgba(121,79,39,0.15)' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#9f927d', fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(121,79,39,0.08)' } },
      axisLabel: { fontSize: 10, color: '#9f927d' },
    },
    series: [
      { name: '执行成功', type: 'bar', data: c.success || [], color: '#6fba2c',
        barMaxWidth: 14, itemStyle: { borderRadius: [3, 3, 0, 0] } },
      { name: '执行失败', type: 'bar', data: c.failed || [], color: '#e05a5a',
        barMaxWidth: 14, itemStyle: { borderRadius: [3, 3, 0, 0] } },
      { name: '新建用例', type: 'bar', data: c.new_cases || [], color: '#889df0',
        barMaxWidth: 14, itemStyle: { borderRadius: [3, 3, 0, 0] } },
    ],
  }
}

function renderChart() {
  if (!instance) return
  instance.setOption(buildOption(), true)
}

function initChart() {
  if (!container.value) return
  instance = echarts.init(container.value)
  renderChart()

  resizeObserver = new ResizeObserver(() => instance?.resize())
  resizeObserver.observe(container.value)
}

onMounted(() => nextTick(initChart))

watch(() => props.chart, () => nextTick(renderChart), { deep: true })

onUnmounted(() => {
  resizeObserver?.disconnect()
  instance?.dispose()
})
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
