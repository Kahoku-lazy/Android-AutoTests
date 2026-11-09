/**
 * [P1] 步骤执行提示 — YAML 带来的 anchor / log 在表格与面板里只读透传，不被编辑洗掉
 */
import { describe, expect, it } from "vitest"
import { toSteps } from "@/modules/case-manager/composables/useCaseSheet"
import { stepHintLines } from "@/modules/case-manager/helpers/step-hints"
import type { CaseStep } from "@/modules/case-manager/types"

const WITH_HINTS: CaseStep = {
  action: "测试亮度功能亮度设置大于70%",
  assertion: "设备日志返回亮度设置成功",
  anchor: { page: "H6810 详情页", entry: "亮度条", target: "亮度滑块" },
  log: { sku: "H6810", port: 7005, keywords: ["lumi_set_success", "lumi_set_success"] },
}

describe("toSteps", () => {
  it("保留页面锚点与日志证据", () => {
    const [step] = toSteps([WITH_HINTS])
    expect(step.anchor).toEqual(WITH_HINTS.anchor)
    expect(step.log).toEqual(WITH_HINTS.log)
  })

  it("没有提示的步骤不产生空节点", () => {
    const [step] = toSteps([{ action: "a", assertion: "b" }])
    expect("anchor" in step).toBe(false)
    expect("log" in step).toBe(false)
  })

  it("拷贝而不是引用，避免改草稿影响原行", () => {
    const [step] = toSteps([WITH_HINTS])
    step.log?.keywords?.push("extra")
    expect(WITH_HINTS.log?.keywords).toHaveLength(2)
  })
})

describe("stepHintLines", () => {
  it("锚点按 page / entry / target 连接", () => {
    const lines = stepHintLines(WITH_HINTS)
    expect(lines[0]).toEqual({
      label: "页面锚点",
      text: "H6810 详情页 · 亮度条 · 亮度滑块",
    })
  })

  it("日志证据给出型号、端口与关键词（重复关键词保留两次）", () => {
    const lines = stepHintLines(WITH_HINTS)
    expect(lines[1]).toEqual({
      label: "日志证据",
      text: "H6810 · 端口 7005 · lumi_set_success / lumi_set_success",
    })
  })

  it("没有提示时返回空数组", () => {
    expect(stepHintLines({ action: "a", assertion: "b" })).toEqual([])
  })
})
