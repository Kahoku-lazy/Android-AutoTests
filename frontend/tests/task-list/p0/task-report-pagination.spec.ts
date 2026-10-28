import { describe, expect, it } from "vitest"
import {
  caseRoundsById,
  reportPageCount,
  reportPageSlice,
} from "@/modules/task-list/helpers/task-detail"

const round = (round_id: number) => ({ round_id, title: `r${round_id}` })

describe("caseRoundsById", () => {
  it("按 round_ids 顺序取轮次", () => {
    const rounds = [round(0), round(1), round(2)]
    expect(caseRoundsById(rounds, [2, 0]).map((r) => r.round_id)).toEqual([2, 0])
  })

  it("找不到的 id 跳过，不报错", () => {
    expect(caseRoundsById([round(0)], [0, 9]).map((r) => r.round_id)).toEqual([0])
    expect(caseRoundsById([], [1])).toEqual([])
  })
})

describe("reportPageCount", () => {
  it("向上取整且至少 1 页", () => {
    expect(reportPageCount(60, 20)).toBe(3)
    expect(reportPageCount(0, 20)).toBe(1)
    expect(reportPageCount(21, 20)).toBe(2)
  })
})

describe("reportPageSlice", () => {
  const items = Array.from({ length: 60 }, (_, i) => i)

  it("第 1 页 20 条", () => {
    expect(reportPageSlice(items, 1, 20)).toHaveLength(20)
    expect(reportPageSlice(items, 1, 20)[0]).toBe(0)
  })

  it("第 2 页是 21–40 条", () => {
    const page2 = reportPageSlice(items, 2, 20)
    expect(page2[0]).toBe(20)
    expect(page2[19]).toBe(39)
  })

  it("越界页码夹到最后一页", () => {
    expect(reportPageSlice(items, 99, 20)[0]).toBe(40)
  })
})
