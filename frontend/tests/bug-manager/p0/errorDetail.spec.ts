import { describe, expect, it } from "vitest"
import { splitErrorDetail } from "@/modules/bug-manager/helpers/errorDetail"

describe("[P0] splitErrorDetail 错误内容行解析", () => {
  it("把「标签：值」拆成含冒号的标签与正文", () => {
    expect(splitErrorDetail("失败原因：模型拒绝（400）")).toEqual([
      { label: "失败原因：", text: "模型拒绝（400）" },
    ])
  })

  it("多行逐行拆分，冒号后的空格不计入正文首字", () => {
    const lines = splitErrorDetail("来源任务：#227 Android-UI-SOP\n任务状态: failed")
    expect(lines).toEqual([
      { label: "来源任务：", text: "#227 Android-UI-SOP" },
      { label: "任务状态:", text: "failed" },
    ])
  })

  it("没有行首标签的行整行当正文", () => {
    expect(splitErrorDetail("  at run (runner.js:12)")).toEqual([
      { label: "", text: "  at run (runner.js:12)" },
    ])
  })

  it("不把 URL / 路径的协议段当标签", () => {
    expect(splitErrorDetail("https://example.com/a:b")).toEqual([
      { label: "", text: "https://example.com/a:b" },
    ])
  })

  it("空文本返回空数组", () => {
    expect(splitErrorDetail("")).toEqual([])
  })
})
