import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import AssistantEditor from "@/modules/ai-assistant/components/AssistantEditor.vue"

const createAssistant = vi.fn(async (_payload?: unknown) => ({ assistant_id: "20261116_K3M" }))

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  listRoleOptions: vi.fn(async () => [{ role_id: "20261116abc", name: "执行配置" }]),
  listToolCatalog: vi.fn(async () => []),
  createAssistant: (payload: unknown) => createAssistant(payload),
}))

vi.mock("element-plus", () => ({ ElMessage: { error: vi.fn() } }))

describe("助手配置弹窗", () => {
  it("头像在名称上方", async () => {
    const wrapper = mount(AssistantEditor)
    await flushPromises()
    const labels = wrapper.findAll(".assistant-field__label").map((node) => node.text())
    expect(labels[0]).toBe("头像")
    expect(labels[1]).toBe("名称")
  })

  it("不选工具也能提交", async () => {
    const wrapper = mount(AssistantEditor)
    await flushPromises()
    await wrapper.find("input.assistant-input").setValue("小助")
    await wrapper.find("select").setValue("20261116abc")
    await wrapper.get("button:last-child").trigger("click")
    await flushPromises()
    expect(createAssistant).toHaveBeenCalledWith(
      expect.objectContaining({ tools: [], display_name: "小助" }),
    )
  })

  it("接口拒绝未知函数时展示错误", async () => {
    createAssistant.mockRejectedValueOnce({ message: "未知工具：not_a_tool" })
    const wrapper = mount(AssistantEditor)
    await flushPromises()
    await wrapper.find("input.assistant-input").setValue("小助")
    await wrapper.find("select").setValue("20261116abc")
    await wrapper.get("button:last-child").trigger("click")
    await flushPromises()
    expect(wrapper.text()).toContain("未知工具")
  })
})
