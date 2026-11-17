<script setup lang="ts">
import { formatSignificant } from "@/shared/animations"
import { useECharts } from "@/shared/composables/useECharts"
import type { ModelDailySeries } from "@/shared/types/dashboard"

const COLORS = ["#4ECDC4", "#F7C948", "#A78BFA", "#FFB5A7", "#89CFF0", "#7C6F83"]

const props = withDefaults(
  defineProps<{
    labels: string[]
    series: ModelDailySeries[]
    unit?: string
  }>(),
  {
    labels: () => [],
    series: () => [],
    unit: "元",
  },
)

function compactNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1).replace(/\.0$/, "")}K`
  return String(value)
}

function buildTooltip(params: { seriesName?: string; marker?: string; dataIndex?: number }[]) {
  if (!params.length) return ""
  const index = params[0].dataIndex ?? 0
  const rows = params.map((item) => {
    const found = props.series.find((row) => row.name === item.seriesName)
    const tokens = found?.tokens[index] ?? 0
    const cost = found?.cost[index] ?? 0
    return `${item.marker ?? ""}${item.seriesName ?? ""}：${compactNumber(tokens)} · ${formatSignificant(cost, 3)} ${props.unit}`
  })
  return [`<b>${props.labels[index] ?? ""}</b>`, ...rows].join("<br/>")
}

function buildOption() {
  return {
    animation: true,
    animationDuration: 800,
    tooltip: { trigger: "axis", textStyle: { color: "#1e1e24" }, formatter: buildTooltip },
    legend: {
      bottom: 0,
      type: "scroll",
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { color: "#1e1e24", fontWeight: 700 },
    },
    grid: { top: 16, right: 8, bottom: 36, left: 8, containLabel: true },
    xAxis: {
      type: "category",
      data: props.labels,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#e8ecf1" } },
      axisLabel: { color: "#999", fontWeight: 600 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#f0ede8" } },
      axisLabel: { color: "#999", formatter: compactNumber },
    },
    series: props.series.map((item, index) => ({
      name: item.name,
      type: "line",
      smooth: 0.25,
      symbol: "circle",
      symbolSize: 6,
      data: item.tokens,
      color: COLORS[index % COLORS.length],
      lineStyle: { width: 3 },
    })),
  }
}

const { container } = useECharts(buildOption, () => [props.labels, props.series, props.unit])
</script>

<template>
  <div ref="container" class="model-line-chart"></div>
</template>

<style scoped>
.model-line-chart {
  width: 100%;
  flex: 1;
  min-height: 220px;
}
</style>
