<script setup lang="ts">
import * as echarts from "echarts"
import { formatSignificant } from "@/shared/animations"
import { useECharts } from "@/shared/composables/useECharts"
import { clockLabel, hourLabel, type HourlyPoint } from "../helpers/hourlyPoints"

export interface TodayUsageChartSeries {
  name: string
  data: HourlyPoint[]
  color: string

  axisIndex: 0 | 1
  unit: "token" | "cost"
}

const props = withDefaults(
  defineProps<{
    series: TodayUsageChartSeries[]
  }>(),
  {
    series: () => [],
  },
)

interface TooltipParam {
  seriesName?: string
  marker?: string
  value?: HourlyPoint | number | null
}

const SLOT_HOURS = 4

function compactNumber(v: number): string {
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M"
  if (v >= 1_000) return (v / 1_000).toFixed(1).replace(/\.0$/, "") + "K"
  return String(v)
}

function seriesText(
  item: TodayUsageChartSeries | undefined,
  raw: number | null | undefined,
): string {
  if (raw === null || raw === undefined || !Number.isFinite(raw)) return "—"
  return item?.unit === "cost" ? `${formatSignificant(raw, 3)} 元` : compactNumber(raw)
}

function costAxisLabel(value: number): string {
  return `${formatSignificant(value, 3)} 元`
}

function pointValue(param: TooltipParam): HourlyPoint | null {
  const value = param.value
  return Array.isArray(value) ? value : null
}

function buildTooltip(raw: TooltipParam[] | TooltipParam): string {
  const list = Array.isArray(raw) ? raw : [raw]
  if (!list.length) return ""
  const point = pointValue(list[0])

  const title = point
    ? Number.isInteger(point[0])
      ? `${hourLabel(point[0])}（${hourLabel(point[0] - 1)}–${hourLabel(point[0])}）`
      : `${clockLabel(point[0])} · 进行中`
    : ""
  const rows = list.map((param) => {
    const item = props.series.find((it) => it.name === param.seriesName)
    return `${param.marker ?? ""}${param.seriesName ?? ""}：${seriesText(item, pointValue(param)?.[1])}`
  })
  return [`<b>${title}</b>`, ...rows].join("<br/>")
}

function buildOption() {
  return {
    animation: true,
    animationDuration: 800,
    animationEasing: "cubicOut",
    animationDurationUpdate: 450,
    tooltip: {
      trigger: "axis",

      triggerOn: "mousemove|click",
      axisPointer: {
        type: "line",
        lineStyle: { color: "#e8ecf1" },
        label: { formatter: (params: { value: number }) => clockLabel(params.value) },
      },
      textStyle: { color: "#1e1e24" },
      formatter: buildTooltip,
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
      type: "value",
      min: 0,
      max: 24,
      interval: SLOT_HOURS,
      axisLine: { lineStyle: { color: "#e8ecf1" } },
      axisTick: { show: false },
      axisLabel: { color: "#999", fontWeight: 600, formatter: hourLabel },
      splitLine: { show: false },
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
        axisLabel: { color: "#999", formatter: costAxisLabel },
      },
    ],
    series: (props.series || []).map((it) => ({
      name: it.name,
      type: "line",
      yAxisIndex: it.axisIndex,
      data: it.data || [],
      color: it.color,

      smooth: 0.25,
      symbol: "circle",
      symbolSize: 5,
      showSymbol: true,
      emphasis: { focus: "series" },
      lineStyle: { width: 3, color: it.color },
      itemStyle: { color: it.color, borderColor: "#fffef5", borderWidth: 2 },

      areaStyle:
        it.unit === "token"
          ? {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "rgba(78,205,196,0.28)" },
                { offset: 1, color: "rgba(78,205,196,0.02)" },
              ]),
            }
          : undefined,
    })),
  }
}

const { container } = useECharts(buildOption, () => [props.series])
</script>

<template>
  <div ref="container" class="today-usage-chart"></div>
</template>

<style scoped>
.today-usage-chart {
  width: 100%;
  flex: 1;
  min-height: 220px;
}
</style>
