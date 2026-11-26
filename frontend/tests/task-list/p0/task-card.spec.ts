import { describe, expect, it } from "vitest"
import { formatTaskCost, formatTaskDuration } from "@/modules/task-list/helpers/task-card"

describe("formatTaskCost / formatTaskDuration", () => {
  it("费用四位小数带元，缺省为 0.0000 元", () => {
    expect(formatTaskCost()).toBe("0.0000 元")
    expect(formatTaskCost(0.01234)).toBe("0.0123 元")
  })

  it("缺开始或结束时耗时为 —", () => {
    expect(formatTaskDuration()).toBe("—")
    expect(formatTaskDuration("2026-09-16 14:00:00")).toBe("—")
    expect(formatTaskDuration("2026-09-16 14:00:00", "2026-09-16 14:01:05")).toBe("≈ 1m 5s")
  })
})
