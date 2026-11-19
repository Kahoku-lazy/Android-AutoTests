import { describe, expect, it } from "vitest"
import { evalBlocked, evalVerdict } from "@/modules/ai-assistant/helpers/eval-view"

describe("评测页", () => {
  it("目标流和团队流直接说明不可评", () => {
    expect(evalBlocked("goal")).toContain("不能评测")
    expect(evalBlocked("team")).toContain("不能评测")
    expect(evalBlocked("sop")).toBe("")
  })

  it("通过只称规则通过", () => {
    expect(evalVerdict(true)).toBe("规则通过")
    expect(evalVerdict(false)).toBe("未通过")
    expect(evalVerdict(true)).not.toContain("真机")
  })
})
