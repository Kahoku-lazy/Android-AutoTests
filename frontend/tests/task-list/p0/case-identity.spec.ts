/**
 * 用例列：一句文案在单元格，多条才在悬停展开。
 */
import { describe, expect, it } from "vitest"
import { caseHover } from "@/modules/task-list/helpers/case-identity"

describe("用例身份悬停", () => {
  it("一条不重复标题", () => {
    expect(caseHover([{ project: "灯", title: "定时" }])).toBe("")
  })

  it("多条按顺序给出项目与标题", () => {
    expect(
      caseHover([
        { project: "灯", title: "定时" },
        { project: "灯", title: "场景" },
      ]),
    ).toBe("灯 / 定时\n灯 / 场景")
  })

  it("缺项目名时标明未命名", () => {
    expect(caseHover([{ title: "甲" }, { project: "", title: "乙" }])).toBe(
      "未命名项目 / 甲\n未命名项目 / 乙",
    )
  })
})
