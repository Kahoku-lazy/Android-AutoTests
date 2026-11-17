import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import AssistantCard from "@/modules/ai-assistant/components/AssistantCard.vue"
import type { AssistantCard as Card, SopWorkflowCard } from "@/modules/ai-assistant/types"

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  avatarUrl: vi.fn(async () => "data:image/jpeg;base64,abc"),
}))

const card: Card = {
  assistant_id: "20261116_K3M",
  display_name: "小助",
  has_avatar: false,
  marker: "moss",
  role_id: "20261116abc",
  role_name: "执行配置",
  tools: [],
}

const workflow: SopWorkflowCard = {
  id: 3,
  name: "桌面检查",
  executor_name: "执行甲",
  verifier_name: "验收乙",
  marker: "moss",
}

describe("助手颜料片", () => {
  it("无头像时只显示名称、笔色圆和配置名", () => {
    const wrapper = mount(AssistantCard, { props: { item: { kind: "assistant", card }, index: 0 } })
    expect(wrapper.text()).toContain("小助")
    expect(wrapper.text()).toContain("执行配置")
    expect(wrapper.find(".assistant-card__swatch").exists()).toBe(true)
    expect(wrapper.find("img").exists()).toBe(false)
    expect(wrapper.text()).not.toContain("20261116")
  })

  it("上边沿有笔色图钉，笔色圆排在名称之上", () => {
    const wrapper = mount(AssistantCard, { props: { item: { kind: "assistant", card }, index: 0 } })
    expect(wrapper.find(".assistant-card__pin").exists()).toBe(true)
    const html = wrapper.html()
    expect(html.indexOf("assistant-card__swatch")).toBeLessThan(
      html.indexOf("assistant-card__name"),
    )
  })

  it("助手形体的第二个动作是对话，且没有便签卡的胶带", () => {
    const wrapper = mount(AssistantCard, { props: { item: { kind: "assistant", card }, index: 0 } })
    expect(wrapper.findAll(".assistant-card__action").map((node) => node.text())).toEqual([
      "配置",
      "对话",
    ])
    expect(wrapper.find(".sop-card__tape").exists()).toBe(false)
  })
})

describe("工作流便签卡", () => {
  it("顶部有胶带，正文分三行：名称、执行者、验收者", () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 1 },
    })
    expect(wrapper.find(".sop-card").exists()).toBe(true)
    expect(wrapper.find(".sop-card__tape").exists()).toBe(true)
    expect(wrapper.find(".sop-card__name").text()).toBe("桌面检查")
    expect(wrapper.findAll(".sop-card__line").map((node) => node.text())).toEqual([
      "执行者：执行甲",
      "验收者：验收乙",
    ])
    expect(wrapper.find(".assistant-card__pin").exists()).toBe(false)
    expect(wrapper.find(".assistant-card__swatch").exists()).toBe(false)
  })

  it("底部一排是上色的配置、任务和同尺寸占位块，共三个元素", () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 1 },
    })
    const trail = wrapper.find(".sop-card__trail")
    expect(trail.find(".sop-card__action--config").text()).toBe("配置")
    expect(trail.find(".sop-card__action--task").text()).toBe("任务")
    expect(trail.find(".sop-card__block").exists()).toBe(true)
    expect(trail.element.children).toHaveLength(3)
  })

  it("占位色块与按钮同排、不可点、不进无障碍树", () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 1 },
    })
    const block = wrapper.find(".sop-card__block")
    expect(block.attributes("aria-hidden")).toBe("true")
    expect(block.element.tagName).toBe("SPAN")
  })

  it("卡片上没有编号与工具清单", () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 2 },
    })
    const text = wrapper.text()
    expect(text).not.toContain("moss")
    expect(text).not.toContain(String(workflow.id))
  })

  it("点任务只抛 activate，由外层决定开哪个弹窗", async () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 0 },
    })
    await wrapper.find(".sop-card__action--task").trigger("click")
    expect(wrapper.emitted("activate")).toHaveLength(1)
    expect(wrapper.emitted("edit")).toBeUndefined()
  })
})
