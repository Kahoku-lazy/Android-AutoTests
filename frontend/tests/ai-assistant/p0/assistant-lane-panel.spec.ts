import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import AssistantLanePanel from "@/modules/ai-assistant/components/AssistantLanePanel.vue"
import type { AssistantThread } from "@/modules/ai-assistant/types"

const lanes: AssistantThread[] = [
  { thread_id: "a", status: "done", title: "第一轮" },
  { thread_id: "b", status: "idle", title: "" },
]

describe("对话栏面板", () => {
  it("空标题按序号补名，选中栏带 is-current", () => {
    const wrapper = mount(AssistantLanePanel, { props: { lanes, currentId: "b" } })
    const items = wrapper.findAll(".lane-panel__lane")
    expect(items[0].text()).toContain("第一轮")
    expect(items[1].text()).toContain("对话 2")
    expect(items[1].classes()).toContain("is-current")
    expect(wrapper.findAll(".lane-panel__wave")).toHaveLength(2)
    expect(wrapper.find(".doodle-btn--teal").exists()).toBe(true)
  })

  it("点重命名切成就地输入框，回车提交", async () => {
    const wrapper = mount(AssistantLanePanel, { props: { lanes, currentId: "a" } })
    await wrapper.findAll(".lane-panel__act")[0].trigger("click")
    const input = wrapper.find(".lane-panel__rename")
    expect(input.exists()).toBe(true)
    await input.setValue("  改过的名字  ")
    await input.trigger("keydown", { key: "Enter" })
    expect(wrapper.emitted("rename")?.[0]).toEqual(["a", "改过的名字"])
    expect(wrapper.find(".lane-panel__rename").exists()).toBe(false)
  })

  it("Esc 取消改名不发事件", async () => {
    const wrapper = mount(AssistantLanePanel, { props: { lanes, currentId: "a" } })
    await wrapper.findAll(".lane-panel__act")[0].trigger("click")
    await wrapper.find(".lane-panel__rename").trigger("keydown", { key: "Escape" })
    expect(wrapper.emitted("rename")).toBeUndefined()
    expect(wrapper.find(".lane-panel__rename").exists()).toBe(false)
  })

  it("点删除发出 remove", async () => {
    const wrapper = mount(AssistantLanePanel, { props: { lanes, currentId: "a" } })
    await wrapper.findAll(".lane-panel__act")[1].trigger("click")
    expect(wrapper.emitted("remove")?.[0]).toEqual(["a"])
  })
})
