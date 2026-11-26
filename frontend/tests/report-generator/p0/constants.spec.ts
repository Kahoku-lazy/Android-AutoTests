import { describe, expect, it } from "vitest"
import {
  EMPTY_TEXT,
  PAGE_HEADER,
  SOURCE_TABS,
  TABLE_COLUMNS,
  sopStatusClass,
  sopStatusLabel,
  sourceLabel,
} from "@/modules/report-generator/constants"

describe("[P0] report-generator workbench copy", () => {
  it("table columns are report-inventory fields", () => {
    expect(TABLE_COLUMNS.map((c) => c.dataIndex)).toEqual([
      "source",
      "identity",
      "relation",
      "outcome",
      "moment",
      "actions",
    ])
  })

  it("source tabs are all / sop / agent", () => {
    expect(SOURCE_TABS.map((tab) => tab.key)).toEqual(["all", "sop", "agent"])
    expect(sourceLabel("sop")).toBe("SOP")
    expect(sourceLabel("agent")).toBe("智能体")
  })

  it("sop terminal statuses map to pass / fail only", () => {
    expect(sopStatusLabel("completed")).toBe("通过")
    expect(sopStatusLabel("success")).toBe("通过")
    expect(sopStatusLabel("failed")).toBe("失败")
    expect(sopStatusClass("completed")).toBe("is-pass")
    expect(sopStatusClass("failed")).toBe("is-fail")
  })

  it("empty copy explains reports appear after completion", () => {
    expect(PAGE_HEADER.subtitle).toContain("执行完成")
    expect(EMPTY_TEXT.hint).toContain("执行完成后生成")
    expect(EMPTY_TEXT.hint).toContain("任务清单")
    expect(EMPTY_TEXT.hint).toContain("平台助手")
    expect(EMPTY_TEXT.hint).not.toContain("执行引擎")
    expect(EMPTY_TEXT.noData).not.toContain("执行引擎")
  })
})
