import type { BugSummary } from "../types"

export const BUG_STATUS_SLICES = [
  { key: "open", label: "待处理", color: "#e0a72e" },
  { key: "resolved", label: "已解决", color: "#4caf50" },
  { key: "ignored", label: "已忽略", color: "#9aa0a6" },
] as const

export const BUG_CATEGORY_BARS = [
  { key: "ui_automation", label: "UI 自动化", color: "#a97cf0" },
  { key: "case_authoring", label: "用例编写", color: "#4ecdc4" },
] as const

export const BUG_DISTRIBUTION_HEIGHT = 260

export function statusSeriesData(summary: BugSummary) {
  return BUG_STATUS_SLICES.map((slice) => ({
    name: slice.label,
    value: summary[slice.key],
    itemStyle: { color: slice.color },
  }))
}

export function categorySeriesData(summary: BugSummary) {
  return BUG_CATEGORY_BARS.map((bar) => ({
    value: summary[bar.key],
    itemStyle: { color: bar.color },
  }))
}

export const BUG_RING_CENTER = { x: "26%", y: "50%" } as const

export const BUG_RING_TEXT_TOP = {
  number: BUG_DISTRIBUTION_HEIGHT / 2 - 9,
  label: BUG_DISTRIBUTION_HEIGHT / 2 + 12,
} as const

export function buildDistributionOption(summary: BugSummary) {
  const statusData = statusSeriesData(summary)
  const categoryData = categorySeriesData(summary)

  return {
    animationDuration: 500,
    tooltip: {
      trigger: "item",
      textStyle: {},
    },
    legend: {
      bottom: 0,
      left: 8,
      data: BUG_STATUS_SLICES.map((slice) => slice.label),
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      textStyle: { color: "#1e1e24", fontWeight: 600 },
    },
    grid: { left: "54%", right: 20, top: 18, bottom: 30, containLabel: true },
    xAxis: {
      type: "value",
      minInterval: 1,
      axisLabel: { color: "#6b6b74" },
      splitLine: { lineStyle: { color: "rgba(30,30,36,0.08)" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: BUG_CATEGORY_BARS.map((bar) => bar.label),
      axisLine: { lineStyle: { color: "rgba(30,30,36,0.15)" } },
      axisTick: { show: false },
      axisLabel: { color: "#1e1e24", fontWeight: 600 },
    },

    graphic: [
      {
        type: "text",
        left: BUG_RING_CENTER.x,
        top: BUG_RING_TEXT_TOP.number,
        style: {
          text: String(summary.total),
          fill: "#1e1e24",
          fontSize: 24,
          fontWeight: 800,
          textAlign: "center",
          textVerticalAlign: "middle",
        },
      },
      {
        type: "text",
        left: BUG_RING_CENTER.x,
        top: BUG_RING_TEXT_TOP.label,
        style: {
          text: "BUG 总数",
          fill: "#6b6b74",
          textAlign: "center",
          textVerticalAlign: "middle",
        },
      },
    ],
    series: [
      {
        name: "处理状态",
        type: "pie",
        radius: ["46%", "70%"],
        center: ["26%", "50%"],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        emphasis: { scale: true, scaleSize: 4 },
        data: statusData,
      },
      {
        name: "任务类型",
        type: "bar",
        barMaxWidth: 18,
        itemStyle: { borderRadius: 6, borderWidth: 1.5, borderColor: "#1e1e24" },
        data: categoryData,
      },
    ],
  }
}
