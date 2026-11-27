import { describe, expect, it } from "vitest"
import {
  creatorPenVars,
  formatTaskCost,
  formatTaskCreator,
  formatTaskDuration,
} from "@/modules/task-list/helpers/task-card"

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

describe("formatTaskCreator", () => {
  it("显示提交人账号名并去掉首尾空白", () => {
    expect(formatTaskCreator("admin")).toBe("admin")
    expect(formatTaskCreator("  Kahoku  ")).toBe("Kahoku")
  })

  it("没有账号名时降级为 —", () => {
    expect(formatTaskCreator()).toBe("—")
    expect(formatTaskCreator("")).toBe("—")
    expect(formatTaskCreator("   ")).toBe("—")
  })
})

describe("creatorPenVars", () => {
  it("不同账号取不同彩笔色", () => {
    expect(creatorPenVars("admin")["--cp-color"]).not.toBe(creatorPenVars("kahoku")["--cp-color"])
  })

  it("同一账号颜色稳定，忽略大小写与首尾空白", () => {
    const base = creatorPenVars("kahoku")
    expect(base["--cp-color"]).toMatch(/^var\(--c-/)
    expect(creatorPenVars("Kahoku")).toEqual(base)
    expect(creatorPenVars("  kahoku ")).toEqual(base)
  })

  it("没有账号名时不套彩色", () => {
    expect(creatorPenVars()).toEqual({})
    expect(creatorPenVars("")).toEqual({})
    expect(creatorPenVars("   ")).toEqual({})
  })
})
