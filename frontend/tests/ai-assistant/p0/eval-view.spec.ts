import { describe, expect, it } from "vitest"
import {
  historyRows,
  methodViews,
  metricLabel,
  missingNotes,
  scoreCards,
  scoreText,
  scoreTone,
  suiteRows,
  trendPoints,
} from "@/modules/ai-assistant/helpers/eval-view"
import type {
  EvalMethod,
  EvalScore,
  EvalSuiteRun,
} from "@/modules/ai-assistant/api/assistants"

function makeScore(id: number, prompt: number, handover: number): EvalScore {
  return {
    id,
    target_kind: "assistant",
    target_id: "a1",
    prompt_fingerprint: `fp-${id}`,
    source_ref: "",
    judge_model: "deepseek-chat",
    created_at: "2026-11-25T08:00:00Z",
    items: [
      { metric_key: "prompt_quality", score: prompt, threshold: 0.5, reason: "角色清晰" },
      { metric_key: "handover_quality", score: handover, threshold: 0.5, reason: "停在详情页" },
    ],
  }
}

describe("评测页", () => {
  it("指标名用中文标签", () => {
    expect(metricLabel("prompt_quality")).toBe("提示词质量")
    expect(metricLabel("handover_quality")).toBe("交接文本质量")
    expect(metricLabel("unknown_metric")).toBe("unknown_metric")
  })

  it("分数保留两位小数", () => {
    expect(scoreText(1)).toBe("1.00")
    expect(scoreText(0.7234)).toBe("0.72")
    expect(scoreText(0)).toBe("0.00")
  })

  it("分数按档位取色，低分走危险色", () => {
    expect(scoreTone(0.9)).toBe("--c-case")
    expect(scoreTone(0.6)).toBe("--c-dashboard")
    expect(scoreTone(0.2)).toBe("--app-marker-red")
    expect(scoreText(0.9)).not.toContain("通过")
  })

  it("评分卡给出分数、理由与未达提示，不给发布结论", () => {
    const cards = scoreCards(makeScore(1, 0.82, 0.46).items)
    expect(cards.map((card) => card.label)).toEqual(["提示词质量", "交接文本质量"])
    expect(cards[0].text).toBe("0.82")
    expect(cards[0].warning).toBe("")
    expect(cards[1].warning).toBe("未达 0.5")
    expect(cards[1].tone).toBe("--app-marker-red")
    expect(JSON.stringify(cards)).not.toContain("未通过")
  })

  it("历史行把分数放指标列、指纹单独放", () => {
    const rows = historyRows([makeScore(9, 0.78, 0.61)])
    expect(rows).toHaveLength(1)
    expect(rows[0].at).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/)
    expect(rows[0].fingerprint).toBe("fp-9")
    expect(rows[0].metrics.map((item) => item.text)).toEqual(["0.78", "0.61"])
  })

  it("缺失指标单独列出原因", () => {
    const score: EvalScore = {
      ...makeScore(2, 0.7, 0.7),
      items: [],
      missing: [{ metric_key: "handover_quality", reason: "没有可用的运行产物" }],
    }
    expect(missingNotes(score)).toEqual([
      { key: "handover_quality", label: "交接文本质量", reason: "没有可用的运行产物" },
    ])
    expect(missingNotes(null)).toEqual([])
  })

  it("趋势点按时间正序且取第一项分数", () => {
    const points = trendPoints([makeScore(2, 0.9, 0.8), makeScore(1, 0.4, 0.3)])
    expect(points.map((point) => point.id)).toEqual([1, 2])
    expect(points.map((point) => point.score)).toEqual([0.4, 0.9])
  })

  it("真题行按步骤达成给判定", () => {
    const run: EvalSuiteRun = {
      id: 3,
      target_id: "assistant:a1",
      created_at: "2026-11-25T08:00:00Z",
      judge_model: "deepseek-chat",
      method_key: "case_suite",
      report_html: "",
      items: [],
      cases: [
        {
          case_id: "c1",
          case_title: "定时功能测试",
          steps_total: 5,
          steps_passed: 5,
          cost_s: 42,
          score: 1,
          reason: "",
        },
        {
          case_id: "c2",
          case_title: "开关与亮度",
          steps_total: 4,
          steps_passed: 2,
          cost_s: 61,
          score: 0.5,
          reason: "",
        },
      ],
    }
    const rows = suiteRows(run)
    expect(rows[0]).toMatchObject({ title: "定时功能测试", passed: "5/5", verdict: "达成" })
    expect(rows[1]).toMatchObject({ title: "开关与亮度", passed: "2/4", verdict: "未达成" })
    expect(rows[1].tone).toBe("--app-marker-red")
    expect(suiteRows(null)).toEqual([])
  })

  it("口径按指标拆成要点，不再是一整段", () => {
    const methods: EvalMethod[] = [
      {
        key: "prompt_quality",
        name: "提示词质量",
        target: "prompt",
        description: "只看提示词本身",
        criteria: "角色是否明确\n流程是否可执行\n工具是否说清",
        threshold: 0.5,
      },
    ]
    const views = methodViews(methods)
    expect(views[0].points).toEqual(["角色是否明确", "流程是否可执行", "工具是否说清"])
    expect(views[0].summary).toBe("只看提示词本身")
  })
})
