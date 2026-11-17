<script setup lang="ts">
import { formatSignificant } from "@/shared/animations"
import { useECharts } from "@/shared/composables/useECharts"

export interface BarLineSeries {
  name: string
  data: number[]
  color: string
}

const props = withDefaults(
  defineProps<{
    labels: string[]
    bars: BarLineSeries
    line: BarLineSeries
    unit?: string
  }>(),
  {
    labels: () => [],
    unit: "元",
  },
)

function compactNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1).replace(/\.0$/, "")}K`
  return String(value)
}

function buildOption() {
  return {
    animation: true,
    animationDuration: 800,
    animationEasing: "cubicOut",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      textStyle: { color: "#1e1e24" },
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 20,
      textStyle: { color: "#1e1e24", fontWeight: 700 },
    },
    grid: { top: 16, right: 8, bottom: 36, left: 8, containLabel: true },
    xAxis: {
      type: "category",
      data: props.labels,
      axisLine: { lineStyle: { color: "#e8ecf1" } },
      axisTick: { show: false },
      axisLabel: { color: "#999", fontWeight: 600 },
    },
    yAxis: [
      {
        type: "value",
        splitLine: { lineStyle: { color: "#f0ede8" } },
        axisLabel: { color: "#999", formatter: compactNumber },
      },
      {
        type: "value",
        splitLine: { show: false },
        axisLabel: {
          color: "#999",
          formatter: (value: number) => `${formatSignificant(value, 3)}`,
        },
      },
    ],
    series: [
      {
        name: props.bars.name,
        type: "bar",
        yAxisIndex: 0,
        data: props.bars.data,
        color: props.bars.color,
        barMaxWidth: 16,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        tooltip: { valueFormatter: (value: number) => compactNumber(value) },
      },
      {
        name: `${props.line.name}（${props.unit}）`,
        type: "line",
        yAxisIndex: 1,
        data: props.line.data,
        color: props.line.color,
        smooth: 0.25,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 3 },
        tooltip: {
          valueFormatter: (value: number) => `${formatSignificant(value, 3)} ${props.unit}`,
        },
      },
    ],
  }
}

const { container } = useECharts(buildOption, () => [
  props.labels,
  props.bars,
  props.line,
  props.unit,
])
</script>

<template>
  <div ref="container" class="dual-axis-chart"></div>
</template>

<style scoped>
.dual-axis-chart {
  width: 100%;
  flex: 1;
  min-height: 220px;
}
</style>
