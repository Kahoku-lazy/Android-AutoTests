<script setup lang="ts">
import { computed } from "vue"
import { useECharts } from "@/shared/composables/useECharts"
import type { ExecutionChart } from "@/shared/types/dashboard"

const props = withDefaults(defineProps<{ chart: ExecutionChart }>(), {
  chart: () => ({ labels: [], success: [], failed: [] }),
})

function buildOption() {
  const c = props.chart
  return {
    animation: true,
    animationDuration: 800,
    animationEasing: "cubicOut",
    animationDurationUpdate: 450,
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      textStyle: { fontSize: 12, color: "#1e1e24" },
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 20,
      textStyle: { fontSize: 12, color: "#1e1e24", fontWeight: 700 },
    },
    grid: { top: 16, right: 8, bottom: 36, left: 8, containLabel: true },
    xAxis: {
      type: "category",
      data: c.labels || [],
      axisLine: { lineStyle: { color: "#e8ecf1" } },
      axisTick: { show: false },
      axisLabel: { fontSize: 12, color: "#999", fontWeight: 600 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#f0ede8" } },
      axisLabel: { fontSize: 12, color: "#999" },
    },
    series: [
      {
        name: "任务成功",
        type: "bar",
        data: c.success || [],
        color: "#6BCB77",
        barMaxWidth: 16,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        animationDelay: (idx) => idx * 40,
      },
      {
        name: "任务失败",
        type: "bar",
        data: c.failed || [],
        color: "#FFB5A7",
        barMaxWidth: 16,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        animationDelay: (idx) => idx * 40 + 60,
      },
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
