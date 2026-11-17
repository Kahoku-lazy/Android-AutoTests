import { describe, expect, it } from "vitest"
import { workflowCards } from "@/modules/ai-assistant/helpers/sop-card"
import type { AssistantCard, SopWorkflow } from "@/modules/ai-assistant/types"

const card = (assistantId: string, name: string, marker: string): AssistantCard => ({
  assistant_id: assistantId,
  display_name: name,
  has_avatar: false,
  marker,
  role_id: `role-${assistantId}`,
  role_name: "配置",
  tools: [],
})

const workflow: SopWorkflow = {
  id: 1,
  name: "桌面检查",
  executor_assistant_id: "20261117_A01",
  verifier_assistant_id: "20261117_B02",
}

describe("工作流卡片展示字段", () => {
  it("取两侧名片的显示名，笔色取执行助手", () => {
    const [tile] = workflowCards(
      [workflow],
      [card("20261117_A01", "执行甲", "rose"), card("20261117_B02", "验收乙", "amber")],
    )
    expect(tile.name).toBe("桌面检查")
    expect(tile.executor_name).toBe("执行甲")
    expect(tile.verifier_name).toBe("验收乙")
    expect(tile.marker).toBe("rose")
  })

  it("名片被删后说明缺口，笔色回落 teal", () => {
    const [tile] = workflowCards([workflow], [card("20261117_B02", "验收乙", "amber")])
    expect(tile.executor_name).toBe("执行助手已不存在")
    expect(tile.marker).toBe("teal")
  })

  it("保持工作流列表顺序", () => {
    const tiles = workflowCards(
      [workflow, { ...workflow, id: 2, name: "第二条" }],
      [card("20261117_A01", "执行甲", "moss"), card("20261117_B02", "验收乙", "moss")],
    )
    expect(tiles.map((tile) => tile.id)).toEqual([1, 2])
  })
})
