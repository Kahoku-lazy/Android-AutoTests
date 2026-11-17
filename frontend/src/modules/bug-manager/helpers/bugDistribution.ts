/**
 * BUG 分布图表配置：把 `summary` 映射成 ECharts option（纯函数，便于单测）。
 *
 * 左侧环形图 = 处理状态（待处理 / 已解决 / 已忽略）
 * 右侧条形图 = 任务类型（UI 自动化 / 用例编写）
 * 数据全部来自列表接口已返回的 `summary`，不额外请求接口，也不在前端重算业务口径。
 */
import type { BugSummary } from "../types"

/** 环形图扇区：顺序即图例顺序 */
export const BUG_STATUS_SLICES = [
  { key: "open", label: "待处理", color: "#e0a72e" },
  { key: "resolved", label: "已解决", color: "#4caf50" },
  { key: "ignored", label: "已忽略", color: "#9aa0a6" },
] as const

/** 条形图分类：与 KPI 卡片同一口径 */
export const BUG_CATEGORY_BARS = [
  { key: "ui_automation", label: "UI 自动化", color: "#a97cf0" },
  { key: "case_authoring", label: "用例编写", color: "#4ecdc4" },
] as const

/** 图表固定高度（与 AppCard 内其它图表一致） */
export const BUG_DISTRIBUTION_HEIGHT = 260

/** 环形图数据：按固定顺序取 summary 中的状态计数 */
export function statusSeriesData(summary: BugSummary) {
  return BUG_STATUS_SLICES.map((slice) => ({
    name: slice.label,
    value: summary[slice.key],
    itemStyle: { color: slice.color },
  }))
}

/** 条形图数据：按固定顺序取 summary 中的类型计数 */
export function categorySeriesData(summary: BugSummary) {
  return BUG_CATEGORY_BARS.map((bar) => ({
    value: summary[bar.key],
    itemStyle: { color: bar.color },
  }))
}

/** 环形圆心的百分比位置（与 series.pie.center 同源） */
export const BUG_RING_CENTER = { x: "26%", y: "50%" } as const

/**
 * 圆心文字的竖直锚点：按图表固定高度算出圆心像素，再据此摆放两段文字。
 * graphic.text 的 `top` 实际落的是字形盒顶部（textVerticalAlign 对 graphic 不生效），
 * 所以要减去各自字高的一半才能让字形正中对上圆心：
 *   数字 24px → 半高约 9px；标签 11px → 半高约 4px，再下移 12px 做行距。
 */
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
    // 环形中心文字：数字用「圆心像素 + textVerticalAlign: middle」精确居中，
    // 标签紧随其下；不再用 44%/54% 这类百分比（会随容器高度漂，导致字偏上）。
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
