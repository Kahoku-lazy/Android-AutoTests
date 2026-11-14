/**
 * 编排卡片纯函数 — 最新判定与上线日期文案
 */
import { describe, expect, it } from "vitest"

import { newestWorkflowKey, releasedLabel } from "@/modules/ai-assistant/helpers/workflow-cards"
import type { WorkflowCard } from "@/modules/ai-assistant/types"

function card(key: string, released_at?: string): WorkflowCard {
  return { key, name: key, summary: "", released_at }
}

describe("[P1] newestWorkflowKey", () => {
  it("取上线日期最新的那张", () => {
    expect(newestWorkflowKey([card("a", "2026-11-11"), card("b", "2026-11-14")])).toBe("b")
  })

  it("没有日期的卡片不参与比较", () => {
    expect(newestWorkflowKey([card("a"), card("b", "2026-11-11")])).toBe("b")
  })

  it("都没有日期时返回空串", () => {
    expect(newestWorkflowKey([card("a"), card("b")])).toBe("")
  })

  it("空列表返回空串", () => {
    expect(newestWorkflowKey([])).toBe("")
  })
})

describe("[P1] releasedLabel", () => {
  it("有日期时拼上线文案", () => {
    expect(releasedLabel(card("a", "2026-11-14"))).toBe("上线于 2026-11-14")
  })

  it("没有日期时返回空串", () => {
    expect(releasedLabel(card("a"))).toBe("")
  })
})
