<script setup lang="ts">
/**
 * TodayUsageChart — 今日 Token 与费用折线（每 4 小时）
 *
 * 横轴是 0–24 的数值轴（刻度每 4 小时一个），折线只画到当前时刻：
 * 已走完的窗口挂在右端刻度，进行中的窗口由后端 `current` 给到当前时刻。
 */
import * as echarts from "echarts"
import { formatSignificant } from "@/shared/animations"
import { useECharts } from "@/shared/composables/useECharts"
import { clockLabel, hourLabel, type HourlyPoint } from "../helpers/hourlyPoints"

export interface TodayUsageChartSeries {
  name: string
  data: HourlyPoint[]
  color: string
  /** 0 = 左轴（token）· 1 = 右轴（费用，元） */
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

// ⚠️ ECharts 渲染在 Canvas 上，不支持 CSS 变量，此处保留色值字面量。
//    token 对照：#1e1e24=--ink · #e8ecf1=--app-border-light · #f0ede8=--app-border-lighter
//    #999=--app-text-secondary · #fffef5=--paper；系列色由调用方按 token 同值传入。
//    字号一律不写：ECharts 默认 12px 与既有柱图一致，且画布字号有「只降不增」门禁。

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
  // 整点 = 已走完的那一小时；非整点 = 进行中的那一小时
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
      // 悬停与点击都能唤出信息：任意时刻都能查
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
    // 数值轴而非类目轴：末端点要落在「现在」（如 11.08），类目轴只能落刻度上
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
      // 曲线：逐小时点连成平滑线，避免直角折线
      smooth: 0.25,
      symbol: "circle",
      symbolSize: 5,
      showSymbol: true,
      emphasis: { focus: "series" },
      lineStyle: { width: 3, color: it.color },
      itemStyle: { color: it.color, borderColor: "#fffef5", borderWidth: 2 },
      // 只给 token 线铺面积，费用线保持细线，避免两块渐变互相盖住
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
