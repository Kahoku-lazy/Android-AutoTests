import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import AssistantEditor from "@/modules/ai-assistant/components/AssistantEditor.vue"

const createAssistant = vi.fn(async (_payload?: unknown) => ({ assistant_id: "20261116_K3M" }))
const deleteAssistant = vi.fn(async (_id?: string) => undefined)
const confirm = vi.fn(async () => undefined)

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  listRoleOptions: vi.fn(async () => [{ role_id: "20261116abc", name: "执行配置" }]),
  listToolCatalog: vi.fn(async () => []),
  createAssistant: (payload: unknown) => createAssistant(payload),
  deleteAssistant: (id: string) => deleteAssistant(id),
  updateAssistant: vi.fn(),
  avatarUrl: vi.fn(async () => ""),
}))

vi.mock("element-plus", () => ({
  ElMessage: { error: vi.fn(), success: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: () => confirm() },
}))

/** 按按钮文字找，不靠位置：删除按钮靠左，创建/保存靠右。 */
function button(wrapper: ReturnType<typeof mount>, label: string) {
  const found = wrapper.findAll("button").find((node) => node.text() === label)
  if (!found) throw new Error(`找不到按钮：${label}`)
  return found
}

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
    await button(wrapper, "创建").trigger("click")
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
    await button(wrapper, "创建").trigger("click")
    await flushPromises()
    expect(wrapper.text()).toContain("未知工具")
  })

  it("新建时没有删除按钮", async () => {
    const wrapper = mount(AssistantEditor)
    await flushPromises()
    expect(wrapper.findAll("button").some((node) => node.text() === "删除")).toBe(false)
  })

  it("编辑时确认后删除该助手", async () => {
    const wrapper = mount(AssistantEditor, {
      props: {
        card: {
          assistant_id: "20261116_K3M",
          display_name: "小助",
          has_avatar: false,
          marker: "teal",
          role_id: "20261116abc",
          role_name: "执行配置",
          tools: [],
        },
      },
    })
    await flushPromises()
    await button(wrapper, "删除").trigger("click")
    await flushPromises()
    expect(deleteAssistant).toHaveBeenCalledWith("20261116_K3M")
    expect(wrapper.emitted("deleted")).toHaveLength(1)
  })

  it("被工作流占用时拒绝删除并点名", async () => {
    deleteAssistant.mockClear()
    const wrapper = mount(AssistantEditor, {
      props: {
        card: {
          assistant_id: "20261116_K3M",
          display_name: "小助",
          has_avatar: false,
          marker: "teal",
          role_id: "20261116abc",
          role_name: "执行配置",
          tools: [],
        },
        workflows: [
          {
            id: 1,
            name: "登录回归",
            executor_assistant_id: "20261116_K3M",
            verifier_assistant_id: "20261116_OTH",
          },
        ],
      },
    })
    await flushPromises()
    await button(wrapper, "删除").trigger("click")
    await flushPromises()
    expect(deleteAssistant).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain("登录回归")
    expect(wrapper.emitted("deleted")).toBeUndefined()
  })

  it("取消确认时不删除", async () => {
    deleteAssistant.mockClear()
    confirm.mockRejectedValueOnce(new Error("cancel"))
    const wrapper = mount(AssistantEditor, {
      props: {
        card: {
          assistant_id: "20261116_K3M",
          display_name: "小助",
          has_avatar: false,
          marker: "teal",
          role_id: "20261116abc",
          role_name: "执行配置",
          tools: [],
        },
      },
    })
    await flushPromises()
    await button(wrapper, "删除").trigger("click")
    await flushPromises()
    expect(deleteAssistant).not.toHaveBeenCalled()
  })
})
