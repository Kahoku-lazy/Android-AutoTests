/** DashboardView 逻辑编排器 — 组合子 composable + 展示辅助 */

import { computed, onMounted, type ComputedRef } from "vue"

import { useDashboardStats, type UseDashboardStatsReturn } from "./composables/useDashboardStats"

import { useDashboardAutoRefresh } from "./composables/useDashboardAutoRefresh"

import { toHourlyPoints, type HourlyPoint } from "./helpers/hourlyPoints"

import type { CaseProjectCardDisplay } from "@/shared/types/dashboard"

import { IconLayers } from "@/shared/icons/index"

// ── 展示配置 ──

/** Dashboard WorkbenchHeader 配置 */

export const PAGE_HEADER = {
  title: "仪表盘",

  subtitle: "自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告",

  icon: "layout-dashboard" as const,

  iconGradient: "linear-gradient(135deg,#F4D35E,#f0c06a)",
}

const PROJECT_CARD_COLORS = ["deep", "sage", "cream", "dust"] as const

// ── 数值格式化助手（单位换算：token → 百万 M）──

/** token 展示数值：百万（M）单位，保留 2 位小数（供 StatsCard value 计数用） */

export function toMillions(n: number): number {
  return Number((n / 1_000_000).toFixed(2))
}

// ── 返回类型接口 ──

interface SeriesDisplay {
  name: string

  data: number[]

  color: string
}

/** 今日 4 小时槽系列：token 走左轴，费用走右轴，点为 [小时, 数值] */
export interface TodayUsageSeriesDisplay {
  name: string

  data: HourlyPoint[]

  color: string

  /** 0 = 左轴（token）· 1 = 右轴（费用，元） */
  axisIndex: 0 | 1

  unit: "token" | "cost"
}

export interface DashboardViewState extends UseDashboardStatsReturn {
  PAGE_HEADER: typeof PAGE_HEADER

  caseProjectCards: ComputedRef<CaseProjectCardDisplay[]>

  tokenSeries: ComputedRef<SeriesDisplay[]>

  costSeries: ComputedRef<SeriesDisplay[]>

  todayUsageSeries: ComputedRef<TodayUsageSeriesDisplay[]>
}

// ── Composable ──

export function useDashboardView(): DashboardViewState {
  const statsComposable = useDashboardStats()

  const caseProjectCards = computed<CaseProjectCardDisplay[]>(() =>
    (statsComposable.stats.value.cases.breakdown ?? []).map((row, index) => ({
      projectId: row.project_id,

      name: row.name,

      total: row.total,

      color: PROJECT_CARD_COLORS[index % PROJECT_CARD_COLORS.length],

      path: `/cases/projects/${row.project_id}`,
    })),
  )

  // ECharts Canvas 不解析 CSS 变量，系列色为字面量（与 tokens.css 同值）：

  // 总 Token #4ECDC4=--c-case · 缓存命中 #A78BFA=--c-element · 费用 #F7C948=--c-dashboard

  const tokenSeries = computed<SeriesDisplay[]>(() => [
    { name: "总 Token", data: statsComposable.aiTokenChart.value.totalTokens, color: "#4ECDC4" },

    { name: "缓存命中", data: statsComposable.aiTokenChart.value.cacheTokens, color: "#A78BFA" },
  ])

  const costSeries = computed<SeriesDisplay[]>(() => [
    { name: "费用", data: statsComposable.deepseekCostChart.value.cost, color: "#F7C948" },
  ])

  // 今日用量折线：token 与费用同色于各自按日图（#4ECDC4=--c-case、#F7C948=--c-dashboard）
  const todayUsageSeries = computed<TodayUsageSeriesDisplay[]>(() => {
    const chart = statsComposable.todayUsageChart.value
    const current = chart.current
    return [
      {
        name: "Token 消耗",
        data: toHourlyPoints(chart.tokens, current?.tokens, current?.hour),
        color: "#4ECDC4",
        axisIndex: 0,
        unit: "token",
      },

      {
        name: "费用",
        data: toHourlyPoints(chart.cost, current?.cost, current?.hour),
        color: "#F7C948",
        axisIndex: 1,
        unit: "cost",
      },
    ]
  })

  onMounted(() => {
    statsComposable.loadData()
  })

  // 页面停留期间静默跟进当日用量，避免图表停在进入页面那一刻
  useDashboardAutoRefresh(statsComposable.refreshSilently)

  return {
    ...statsComposable,

    PAGE_HEADER,

    caseProjectCards,

    tokenSeries,

    costSeries,

    todayUsageSeries,
  }
}
