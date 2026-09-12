/** DashboardView 逻辑编排器 — 组合子 composable + 展示辅助 */
import { computed, onMounted, type ComputedRef } from 'vue'
import { useDashboardStats, type UseDashboardStatsReturn } from './composables/useDashboardStats'
import type {
  CaseBreakdownItem,
  ElementBreakdownItem,
  CaseBreakdownDisplay,
  ElementBreakdownDisplay,
} from '@/shared/types/dashboard'
import {
  IconDevice,
  IconTarget,
  IconZap,
  IconLayers,
} from '@/shared/icons/index'

// ── 展示配置 ──

/** Dashboard WorkbenchHeader 配置 */
export const PAGE_HEADER = {
  title: '仪表盘',
  subtitle: '自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告',
  icon: 'layout-dashboard' as const,
  iconGradient: 'linear-gradient(135deg,#F4D35E,#f0c06a)',
}

const CASE_BREAKDOWN: CaseBreakdownDisplay[] = [
  { type: 'ui_automation', label: 'Android用例', color: 'deep', icon: IconDevice },
  { type: 'web_automation', label: 'Web用例', color: 'sage', icon: IconTarget },
  { type: 'api_testing', label: 'API用例', color: 'cream', icon: IconZap },
  { type: 'storage', label: '功能业务', color: 'dust', icon: IconLayers },
]

const ELEMENT_BREAKDOWN: ElementBreakdownDisplay[] = [
  { type: 'android', label: 'Android元素', color: 'deep', icon: IconDevice },
  { type: 'web', label: 'Web元素', color: 'sage', icon: IconTarget },
  { type: 'api', label: 'API接口', color: 'cream', icon: IconZap },
]

// ── 数值格式化助手（单位换算：累计 token → 百万 M；平均每任务 token → 千 K）──

/** 累计 token 展示数值：百万（M）单位，保留 2 位小数（供 StatsCard value 计数用） */
export function toMillions(n: number): number {
  return Number((n / 1_000_000).toFixed(2))
}

/** 平均每任务 token 展示数值：千（K）单位，保留 1 位小数 */
export function toK(n: number): number {
  return Number((n / 1_000).toFixed(1))
}

// ── 返回类型接口 ──

interface SeriesDisplay {
  name: string
  data: number[]
  color: string
}

export interface DashboardViewState extends UseDashboardStatsReturn {
  PAGE_HEADER: typeof PAGE_HEADER
  caseBreakdown: CaseBreakdownDisplay[]
  elementBreakdown: ElementBreakdownDisplay[]
  getBreakdownItem: (type: string) => CaseBreakdownItem
  getElementItem: (type: string) => ElementBreakdownItem
  tokenSeries: ComputedRef<SeriesDisplay[]>
  costSeries: ComputedRef<SeriesDisplay[]>
  roleBreakdown: ComputedRef<{ today: string; total: string }>
}

// ── Composable ──

export function useDashboardView(): DashboardViewState {
  const statsComposable = useDashboardStats()

  function getBreakdownItem(type: string): CaseBreakdownItem {
    return statsComposable.stats.value.cases.breakdown?.find((b) => b.type === type) || { type, total: 0, enabled: 0 }
  }

  function getElementItem(type: string): ElementBreakdownItem {
    return statsComposable.stats.value.elements.typeBreakdown?.find((b) => b.type === type) || { type, total: 0 }
  }

  // ECharts Canvas 不解析 CSS 变量，系列色为字面量（与 tokens.css 同值）：
  // 总 Token #4ECDC4=--c-case · 缓存命中 #A78BFA=--c-element · 费用 #F7C948=--c-dashboard
  const tokenSeries = computed<SeriesDisplay[]>(() => [
    { name: '总 Token', data: statsComposable.aiTokenChart.value.totalTokens, color: '#4ECDC4' },
    { name: '缓存命中', data: statsComposable.aiTokenChart.value.cacheTokens, color: '#A78BFA' },
  ])

  const costSeries = computed<SeriesDisplay[]>(() => [
    { name: '费用', data: statsComposable.deepseekCostChart.value.cost, color: '#F7C948' },
  ])

  const ROLE_LABELS: Record<string, string> = { planner: '规划', executor: '执行', verifier: '验证' }

  const roleBreakdown = computed(() => {
    const byRole = statsComposable.stats.value.aiUsage.byRole ?? { today: {}, total: {} }
    const fmt = (metric: Record<string, { input_tokens?: number }>) =>
      ['planner', 'executor', 'verifier']
        .map((role) => {
          const v = metric[role]
          const m = ((v?.input_tokens ?? 0) / 1000000).toFixed(2)
          return `${ROLE_LABELS[role] || role} ${m}M`
        })
        .join(' · ')
    return { today: fmt(byRole.today ?? {}), total: fmt(byRole.total ?? {}) }
  })

  onMounted(() => {
    statsComposable.loadData()
  })

  return {
    ...statsComposable,
    PAGE_HEADER,
    caseBreakdown: CASE_BREAKDOWN,
    elementBreakdown: ELEMENT_BREAKDOWN,
    getBreakdownItem,
    getElementItem,
    tokenSeries,
    costSeries,
    roleBreakdown,
  }
}
