import { describe, expect, it } from "vitest"
import { sopSubmittedMessage } from "@/modules/ai-assistant/helpers/sop-form"

describe("SOP 提交成功提示", () => {
  it("正文带任务编号，行动入口文案单独给出", () => {
    const { text, action } = sopSubmittedMessage(18)
    expect(text).toContain("18")
    expect(text).not.toContain("去任务清单")
    expect(action).toBe("去任务清单")
  })
})
