import { describe, expect, it } from "vitest"
import { parseCaseTitles } from "@/modules/ai-assistant/helpers/yaml-case-titles"

describe("parseCaseTitles", () => {
  it("读取用例列表的标题并保持顺序", () => {
    const text = `
- title: 甲
  steps:
    - action: a
      assert: b
- title: 乙
  steps:
    - action: c
      assert: d
`
    expect(parseCaseTitles(text)).toEqual({ titles: ["甲", "乙"], error: "" })
  })

  it("支持单条用例映射", () => {
    const text = "title: 只有一条\nsteps:\n  - action: a\n    assert: b\n"
    expect(parseCaseTitles(text)).toEqual({ titles: ["只有一条"], error: "" })
  })

  it("缺 title 时给出可读错误", () => {
    const result = parseCaseTitles("- steps:\n    - action: a\n      assert: b\n")
    expect(result.titles).toEqual([])
    expect(result.error).toContain("title")
  })

  it("无法解析时给出可读错误", () => {
    const result = parseCaseTitles(":\n  - [")
    expect(result.titles).toEqual([])
    expect(result.error).toContain("YAML")
  })

  it("空文件给空态错误", () => {
    const result = parseCaseTitles("")
    expect(result.titles).toEqual([])
    expect(result.error).toContain("没有可用用例")
  })
})
