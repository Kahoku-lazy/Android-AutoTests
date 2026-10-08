/**
 * [P0] 模型能力标注：多模态标记文案 + 「已知纯文本」判定
 */
import { describe, expect, it } from "vitest"
import {
  isKnownTextOnly,
  modelOptionLabel,
  type ModelOption,
} from "@/modules/ai-assistant/helpers/model-capability"

const OPTIONS: ModelOption[] = [
  { name: "deepseek-flash", multimodal: true },
  { name: "deepseek-v4-pro" },
]

describe("模型能力标注", () => {
  it("多模态模型标「支持图片」，纯文本模型标「纯文本」", () => {
    expect(modelOptionLabel(OPTIONS[0])).toBe("deepseek-flash（多模态 · 支持图片）")
    expect(modelOptionLabel(OPTIONS[1])).toBe("deepseek-v4-pro（纯文本）")
  })

  it("只识别清单内已知的纯文本模型；未知模型与空值都不提示", () => {
    expect(isKnownTextOnly(OPTIONS, "deepseek-v4-pro")).toBe(true)
    expect(isKnownTextOnly(OPTIONS, "deepseek-flash")).toBe(false)
    expect(isKnownTextOnly(OPTIONS, "自建视觉模型")).toBe(false)
    expect(isKnownTextOnly(OPTIONS, "")).toBe(false)
    expect(isKnownTextOnly(OPTIONS, undefined)).toBe(false)
  })
})
