import { describe, expect, it } from "vitest"
import {
  blankForm,
  formFromCard,
  toToolSelection,
} from "@/modules/ai-assistant/helpers/editor-form"
import { markerVars } from "@/modules/ai-assistant/helpers/marker"
import type { AssistantCard } from "@/modules/ai-assistant/types"

const card: AssistantCard = {
  assistant_id: "20261116_K3M",
  display_name: "小助",
  has_avatar: false,
  marker: "moss",
  role_id: "20261116abc",
  role_name: "执行配置",
  tools: [{ domain: "adb", preset: "readonly", add: [], remove: ["reboot"] }],
}

describe("助手配置表单数据", () => {
  it("空白表单不挂工具", () => {
    const form = blankForm()
    expect(toToolSelection(form)).toEqual([])
  })

  it("由名片回填工具域与预设", () => {
    const form = formFromCard(card)
    expect(form.displayName).toBe("小助")
    expect(form.roleId).toBe("20261116abc")
    expect(toToolSelection(form)).toEqual([
      { domain: "adb", preset: "readonly", add: [], remove: ["reboot"] },
    ])
  })

  it("笔色映射到模块令牌，未知键回落 teal", () => {
    expect(markerVars("moss")).toEqual({ "--assistant-marker": "var(--assistant-marker-moss)" })
    expect(markerVars("unknown")).toEqual({ "--assistant-marker": "var(--assistant-marker-teal)" })
  })
})
