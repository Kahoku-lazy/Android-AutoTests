import { formatDateTime } from "@/shared/helpers/datetime"
import { EVAL_METRIC_LABELS } from "../constants"
import type {
  EvalCase,
  EvalMethod,
  EvalScore,
  EvalScoreItem,
  EvalSuiteRun,
} from "../api/assistants"

export function metricLabel(key: string): string {
  return EVAL_METRIC_LABELS[key] || key
}

export function scoreText(value: number): string {
  return value.toFixed(2)
}

export function scoreTone(value: number): string {
  if (value >= 0.8) return "--c-case"
  if (value >= 0.5) return "--c-dashboard"
  return "--app-marker-red"
}

export interface MetricChipView {
  key: string
  label: string
  text: string
  tone: string
}

export interface ScoreCardView extends MetricChipView {
  reason: string
  warning: string
}

export interface MissingNoteView {
  key: string
  label: string
  reason: string
}

export interface HistoryRowView {
  id: number
  at: string
  fingerprint: string
  judge: string
  metrics: MetricChipView[]
}

export interface SuiteRowView {
  id: string
  title: string
  passed: string
  cost: string
  verdict: string
  tone: string
}

export interface CaseRowView {
  id: number
  title: string
  stepCount: number
}

export interface MethodView {
  key: string
  name: string
  summary: string
  points: string[]
}

export interface TrendPointView {
  id: number
  label: string
  score: number
}

function metricChip(key: string, score: number): MetricChipView {
  return { key, label: metricLabel(key), text: scoreText(score), tone: scoreTone(score) }
}

export function scoreCards(items: EvalScoreItem[] = []): ScoreCardView[] {
  return items.map((item) => ({
    ...metricChip(item.metric_key, item.score),
    reason: item.reason,
    warning: item.score < item.threshold ? `未达 ${item.threshold.toFixed(1)}` : "",
  }))
}

export function missingNotes(score: EvalScore | null = null): MissingNoteView[] {
  return (score?.missing || []).map((item) => ({
    key: item.metric_key,
    label: metricLabel(item.metric_key),
    reason: item.reason,
  }))
}

export function historyRows(scores: EvalScore[] = []): HistoryRowView[] {
  return scores.map((row) => ({
    id: row.id,
    at: formatDateTime(row.created_at, { precision: "minute" }),
    fingerprint: row.prompt_fingerprint,
    judge: row.judge_model,
    metrics: row.items.map((item) => metricChip(item.metric_key, item.score)),
  }))
}

export function suiteRows(run: EvalSuiteRun | null = null): SuiteRowView[] {
  if (!run) return []
  return run.cases.map((row) => {
    const done = row.steps_total > 0 && row.steps_passed >= row.steps_total
    return {
      id: String(row.case_id),
      title: row.case_title,
      passed: `${row.steps_passed}/${row.steps_total}`,
      cost: `${row.cost_s}s`,
      verdict: done ? "达成" : "未达成",
      tone: done ? "--c-device" : "--app-marker-red",
    }
  })
}

export function trendPoints(scores: EvalScore[] = []): TrendPointView[] {
  return [...scores].reverse().map((row) => ({
    id: row.id,
    label: formatDateTime(row.created_at, { precision: "minute" }),
    score: row.items[0]?.score ?? 0,
  }))
}

export function caseRows(cases: EvalCase[] = []): CaseRowView[] {
  return cases.map((item) => ({
    id: item.id,
    title: item.title,
    stepCount: item.steps.length || item.step_count || 0,
  }))
}

export function replaceCase(cases: EvalCase[], next: EvalCase): EvalCase[] {
  return cases.map((item) => (item.id === next.id ? next : item))
}

export function appendCase(cases: EvalCase[], next: EvalCase): EvalCase[] {
  return [next, ...cases.filter((item) => item.id !== next.id)]
}

export function dropCase(cases: EvalCase[], caseId: number): EvalCase[] {
  return cases.filter((item) => item.id !== caseId)
}

export function methodViews(methods: EvalMethod[] = []): MethodView[] {
  return methods.map((item) => ({
    key: item.key,
    name: item.name,
    summary: item.description,
    points: (item.criteria || "")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean),
  }))
}
