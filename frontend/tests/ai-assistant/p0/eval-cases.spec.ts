import { describe, expect, it } from "vitest"
import {
  appendCase,
  caseRows,
  dropCase,
  replaceCase,
} from "@/modules/ai-assistant/helpers/eval-view"
import type { EvalCase } from "@/modules/ai-assistant/api/assistants"

function makeCase(id: number, title: string, steps: number): EvalCase {
  return {
    id,
    title,
    note: "",
    enabled: true,
    steps: Array.from({ length: steps }, (_, index) => ({
      action: `动作 ${index + 1}`,
      assertion: `断言 ${index + 1}`,
      anchor: { page: "首页" },
    })),
  }
}

describe("题库页数据构造", () => {
  it("题目行带编号、题目与步数", () => {
    const rows = caseRows([makeCase(7, "定时功能测试", 5)])
    expect(rows).toEqual([{ id: 7, title: "定时功能测试", stepCount: 5 }])
  })

  it("没有步骤时退回 step_count", () => {
    const rows = caseRows([{ ...makeCase(8, "空题目", 0), step_count: 3 }])
    expect(rows[0].stepCount).toBe(3)
  })

  it("保存只替换被编辑的那一行", () => {
    const cases = [makeCase(1, "甲", 1), makeCase(2, "乙", 2), makeCase(3, "丙", 1)]
    const next = replaceCase(cases, makeCase(2, "乙改", 4))
    expect(next.map((item) => item.id)).toEqual([1, 2, 3])
    expect(next[1].title).toBe("乙改")
    expect(next[0].title).toBe("甲")
    expect(next[2].title).toBe("丙")
  })

  it("新建插到最前且不重复", () => {
    const cases = [makeCase(1, "甲", 1)]
    const next = appendCase(cases, makeCase(2, "乙", 1))
    expect(next.map((item) => item.id)).toEqual([2, 1])
    const again = appendCase(next, makeCase(2, "乙改", 2))
    expect(again.map((item) => item.id)).toEqual([2, 1])
    expect(again[0].title).toBe("乙改")
  })

  it("删除只移除目标行", () => {
    const cases = [makeCase(1, "甲", 1), makeCase(2, "乙", 1)]
    expect(dropCase(cases, 1).map((item) => item.id)).toEqual([2])
    expect(dropCase(cases, 99)).toHaveLength(2)
  })
})
