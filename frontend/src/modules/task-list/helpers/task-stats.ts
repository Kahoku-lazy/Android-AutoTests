/** task-stats — 任务统计的展示口径：成功率文案、四类结果占比与分智能体柱状图（纯函数） */
import type { TaskStats } from "@/shared/types/ai"

export type OutcomeKey = "success" | "failed" | "interrupted" | "cancelled"

export interface OutcomeSlice {
  key: OutcomeKey
  label: string
  value: number
  /** ECharts 画布色（= 对应模块令牌；画布不支持 CSS 变量） */
  color: string
  percent: number
}

/** 四类结果的来源：总体统计与单个智能体统计都满足这个形状 */
export interface OutcomeSource {
  success: number
  failed: number
  interrupted: number
  cancelled: number
}

/** 成功率来源：只需要已结束条数与成功率两个字段 */
export interface RateSource {
  finished: number
  success_rate: number
}

/** 一张柱状图卡片：标题 / 副标题 / 四类结果 */
export interface ResultBarCard {
  key: string
  title: string
  caption: string
  items: OutcomeSlice[]
}

/**
 * 四类结果色：绿=成功 · 桃粉=失败 · 柠黄=中断 · 灰紫=取消。
 * 与 tokens.css 同值：--c-device #6BCB77 · --c-runner #FFB5A7 ·
 * --c-dashboard #F7C948 · --c-report #7C6F83。
 */
export const OUTCOME_COLORS: Record<OutcomeKey, string> = {
  success: "#6BCB77",
  failed: "#FFB5A7",
  interrupted: "#F7C948",
  cancelled: "#7C6F83",
}

const OUTCOME_LABELS: { key: OutcomeKey; label: string }[] = [
  { key: "success", label: "成功" },
  { key: "failed", label: "失败" },
  { key: "interrupted", label: "中断" },
  { key: "cancelled", label: "取消" },
]

/** 成功率文案：没有已结束任务时给「—」，不显示 0% */
export function successRateText(stats: RateSource | null): string {
  if (!stats || stats.finished <= 0) return "—"
  const rate = Number(stats.success_rate) || 0
  return `${Number.isInteger(rate) ? rate.toFixed(0) : rate.toFixed(1)}%`
}

/** 四类结果切片：数量为 0 也保留（图例要说明该类别为空） */
export function outcomeSlices(stats: OutcomeSource | null): OutcomeSlice[] {
  const values: Record<OutcomeKey, number> = {
    success: stats?.success ?? 0,
    failed: stats?.failed ?? 0,
    interrupted: stats?.interrupted ?? 0,
    cancelled: stats?.cancelled ?? 0,
  }
  const total = OUTCOME_LABELS.reduce((sum, item) => sum + values[item.key], 0)
  return OUTCOME_LABELS.map((item) => ({
    key: item.key,
    label: item.label,
    value: values[item.key],
    color: OUTCOME_COLORS[item.key],
    percent: total ? Math.round((values[item.key] / total) * 1000) / 10 : 0,
  }))
}

/** 占比图是否有可画的扇区（四类全 0 时走空态） */
export function hasOutcomeData(stats: TaskStats | null): boolean {
  return outcomeSlices(stats).some((item) => item.value > 0)
}

/**
 * 柱状图卡片序列：第一张是总体「结果数量」，之后每个可见智能体一张。
 *
 * 智能体清单来自统计接口（含尚未跑过任务的智能体），因此新增智能体后
 * 这里会自动多一张卡片，不需要改前端。
 */
export function resultBarCards(stats: TaskStats | null): ResultBarCard[] {
  const cards: ResultBarCard[] = [
    {
      key: "all",
      title: "结果数量",
      caption: `共 ${stats?.total ?? 0} 条 · 执行中 ${stats?.running ?? 0} 条`,
      items: outcomeSlices(stats),
    },
  ]
  for (const agent of stats?.agents ?? []) {
    cards.push({
      key: `agent-${agent.id}`,
      title: agent.name || `智能体 ${agent.id}`,
      caption: `共 ${agent.total} 条 · 执行中 ${agent.running} · 成功率 ${successRateText(agent)}`,
      items: outcomeSlices(agent),
    })
  }
  return cards
}
