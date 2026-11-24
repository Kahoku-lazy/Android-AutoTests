import type { TaskStats } from "@/shared/types/ai"

export type OutcomeKey = "success" | "failed" | "interrupted" | "cancelled"

export interface OutcomeSlice {
  key: OutcomeKey
  label: string
  value: number

  color: string
  percent: number
}

export interface OutcomeSource {
  success: number
  failed: number
  interrupted: number
  cancelled: number
}

export interface RateSource {
  finished: number
  success_rate: number
}

export interface ResultBarCard {
  key: string
  title: string
  caption: string
  items: OutcomeSlice[]
}

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

export function successRateText(stats: RateSource | null): string {
  if (!stats || stats.finished <= 0) return "—"
  const rate = Number(stats.success_rate) || 0
  return `${Number.isInteger(rate) ? rate.toFixed(0) : rate.toFixed(1)}%`
}

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

export function hasOutcomeData(stats: TaskStats | null): boolean {
  return outcomeSlices(stats).some((item) => item.value > 0)
}

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
