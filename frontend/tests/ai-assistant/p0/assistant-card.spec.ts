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
  orchestration: "sop",
  kind: "ui_automation",
  executor_name: "执行甲",
  verifier_name: "验收乙",
  leader_name: "",
  member_count: 0,
  marker: "moss",
}

describe("助手颜料片", () => {
  it("无头像时只显示名称、笔色圆和配置名", () => {
    const wrapper = mount(AssistantCard, { props: { item: { kind: "assistant", card }, index: 0 } })
    expect(wrapper.text()).toContain("小助")
    expect(wrapper.text()).toContain("执行配置")
    expect(wrapper.find(".assistant-card__swatch").exists()).toBe(true)
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "draft" } },
        index: 0,
      },
    })
    expect(draft.text()).toContain("草稿")
    expect(wrapper.find("img").exists()).toBe(false)
    expect(wrapper.text()).not.toContain("20261116")
  })

  it("非作者不显示配置入口", () => {
    const wrapper = mount(AssistantCard, {
      props: { item: { kind: "assistant", card }, index: 0, canEdit: false },
    })
    expect(wrapper.find(".assistant-card__action--config").exists()).toBe(false)
    expect(wrapper.text()).toContain("对话")
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

  it("草稿卡的发布在卡内第三位，已发布卡没有发布", () => {
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "draft" } },
        index: 0,
        canPublish: true,
      },
    })
    const actions = draft.find(".assistant-card__actions")
    expect(actions.findAll(".assistant-card__action").map((node) => node.text())).toEqual([
      "配置",
      "对话",
      "发布",
    ])
    expect(draft.findAll(".assistant-card__actions")).toHaveLength(1)
    expect(actions.find(".assistant-card__action--publish").exists()).toBe(true)

    const published = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "published" } },
        index: 0,
        canPublish: true,
      },
    })
    expect(published.findAll(".assistant-card__action").map((node) => node.text())).toEqual([
      "配置",
      "对话",
    ])
  })

  it("草稿标识是独立胶囊，不写进名称", () => {
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "draft" } },
        index: 0,
        canPublish: true,
      },
    })
    expect(draft.find(".assistant-card__name").text()).toBe("小助")
    expect(draft.find(".assistant-card__chip").text()).toBe("草稿")
  })

  it("点发布只抛 publish", async () => {
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "draft" } },
        index: 0,
        canPublish: true,
      },
    })
    await draft.find(".assistant-card__action--publish").trigger("click")
    expect(draft.emitted("publish")).toHaveLength(1)
    expect(draft.emitted("edit")).toBeUndefined()
    expect(draft.emitted("activate")).toBeUndefined()
  })

  it("发布失败只在该卡显示原因，卡片其余内容还在", () => {
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "assistant", card: { ...card, release_state: "draft" } },
        index: 0,
        canPublish: true,
        error: "发布被拒：两侧名片都要先发布",
      },
    })
    expect(draft.find(".assistant-card__error").text()).toContain("两侧名片都要先发布")
    expect(draft.find(".assistant-card__name").text()).toBe("小助")
    expect(draft.find(".assistant-card__action--publish").exists()).toBe(true)
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

    const reader = mount(AssistantCard, {
      props: { item: { kind: "workflow", card: workflow }, index: 1, canEdit: false },
    })
    expect(reader.find(".sop-card__action--config").exists()).toBe(false)
    expect(reader.text()).toContain("任务")
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

  it("草稿工作流卡的发布替换占位块，已发布卡仍留占位块", async () => {
    const draft = mount(AssistantCard, {
      props: {
        item: { kind: "workflow", card: { ...workflow, release_state: "draft" } },
        index: 0,
        canPublish: true,
      },
    })
    const trail = draft.find(".sop-card__trail")
    expect(trail.element.children).toHaveLength(3)
    expect(Array.from(trail.element.children).map((node) => node.textContent?.trim())).toEqual([
      "配置",
      "任务",
      "发布",
    ])
    expect(trail.find(".sop-card__block").exists()).toBe(false)
    expect(draft.find(".sop-card__chip").text()).toBe("草稿")

    await draft.find(".sop-card__action--publish").trigger("click")
    expect(draft.emitted("publish")).toHaveLength(1)

    const published = mount(AssistantCard, {
      props: {
        item: { kind: "workflow", card: { ...workflow, release_state: "published" } },
        index: 0,
        canPublish: true,
      },
    })
    expect(published.find(".sop-card__action--publish").exists()).toBe(false)
    expect(published.find(".sop-card__block").exists()).toBe(true)
    expect(published.find(".sop-card__chip").exists()).toBe(false)
  })
})
