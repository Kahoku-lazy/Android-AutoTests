import { computed, onMounted, type ComputedRef } from "vue"

import { useDashboardStats, type UseDashboardStatsReturn } from "./composables/useDashboardStats"

import { useDashboardAutoRefresh } from "./composables/useDashboardAutoRefresh"

import { toHourlyPoints, type HourlyPoint } from "./helpers/hourlyPoints"

import type { CaseProjectCardDisplay } from "@/shared/types/dashboard"

import { IconLayers } from "@/shared/icons/index"

export const PAGE_HEADER = {
  title: "仪表盘",

  subtitle: "智能化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告",

  icon: "layout-dashboard" as const,

  iconGradient: "linear-gradient(135deg,#F4D35E,#f0c06a)",
}

const PROJECT_CARD_COLORS = ["deep", "sage", "cream", "dust"] as const

export function toMillions(n: number): number {
  return Number((n / 1_000_000).toFixed(2))
}

interface SeriesDisplay {
  name: string

  data: number[]

  color: string
}

export interface TodayUsageSeriesDisplay {
  name: string

  data: HourlyPoint[]

  color: string

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

  const tokenSeries = computed<SeriesDisplay[]>(() => [
    { name: "总 Token", data: statsComposable.aiTokenChart.value.totalTokens, color: "#4ECDC4" },

    { name: "缓存命中", data: statsComposable.aiTokenChart.value.cacheTokens, color: "#A78BFA" },
  ])

  const costSeries = computed<SeriesDisplay[]>(() => [
    { name: "费用", data: statsComposable.deepseekCostChart.value.cost, color: "#F7C948" },
  ])

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
