/** AI 助手看板：每个可见 Agent 一张卡，用例编写 Agent 读取 case_authoring 线路。 */
import { describe, expect, it } from "vitest"
import { displayedAssistantCards } from "@/modules/ai-assistant/helpers/assistant-cards"
import type { AgentRecord } from "@/shared/types/ai"

function agent(overrides: Partial<AgentRecord>): AgentRecord {
  return {
    id: 1,
    name: "Agent",
    status: "active",
    ...overrides,
  }
}

describe("[P0] displayedAssistantCards", () => {
  it("设备执行与用例编写各一张卡，职责跟随 task_kind", () => {
    const cards = displayedAssistantCards([
      agent({
        id: 10,
        name: "Agent-01",
        task_kind: "device_control",
        route_configs: { device_control: { name: "Agent-01号" } },
      }),
      agent({
        id: 11,
        name: "Agent-02",
        task_kind: "case_authoring",
        route_configs: { case_authoring: { name: "Agent-02" } },
      }),
    ])

    expect(cards).toHaveLength(2)
    expect(cards[0]).toMatchObject({ agentId: 10, name: "Agent-01号", duty: "UI自动化" })
    expect(cards[1]).toMatchObject({ agentId: 11, name: "Agent-02", duty: "测试用例编写" })
  })

  it("用例编写 Agent 缺少 case_authoring 线路时回退 device_control 名称", () => {
    const [card] = displayedAssistantCards([
      agent({
        id: 11,
        name: "Agent-02",
        task_kind: "case_authoring",
        route_configs: { device_control: { name: "回退名称" } },
      }),
    ])
    expect(card.name).toBe("回退名称")
  })
})
