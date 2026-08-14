/** DashboardView 逻辑编排器 — 组合子 composable + 展示辅助 */
import { onMounted } from 'vue'
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

// ── 返回类型接口 ──

export interface DashboardViewState extends UseDashboardStatsReturn {
  PAGE_HEADER: typeof PAGE_HEADER
  caseBreakdown: CaseBreakdownDisplay[]
  elementBreakdown: ElementBreakdownDisplay[]
  getBreakdownItem: (type: string) => CaseBreakdownItem
  getElementItem: (type: string) => ElementBreakdownItem
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
  }
}
