import { flushPromises, mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ElMessageBox } from "element-plus"
import SopWorkflowEditor from "@/modules/ai-assistant/components/SopWorkflowEditor.vue"
import type { AssistantCard, SopWorkflow } from "@/modules/ai-assistant/types"

const createWorkflow = vi.fn(async (_payload?: unknown) => ({ id: 9 }))
const updateWorkflow = vi.fn(async (_id?: number, _payload?: unknown) => ({ id: 9 }))
const removeWorkflow = vi.fn(async (_id?: number) => undefined)

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  createSopWorkflow: (payload: unknown) => createWorkflow(payload),
  updateSopWorkflow: (id: number, payload: unknown) => updateWorkflow(id, payload),
  deleteSopWorkflow: (id: number) => removeWorkflow(id),
}))

vi.mock("element-plus", () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn(async () => "confirm") },
}))

const cards: AssistantCard[] = [
  {
    assistant_id: "20261117_A01",
    display_name: "执行甲",
    has_avatar: false,
    marker: "teal",
    role_id: "role-a",
    role_name: "配置甲",
    tools: [],
  },
  {
    assistant_id: "20261117_B02",
    display_name: "验收乙",
    has_avatar: false,
    marker: "rose",
    role_id: "role-b",
    role_name: "配置乙",
    tools: [],
  },
]

const workflow: SopWorkflow = {
  id: 7,
  name: "桌面检查",
  executor_assistant_id: "20261117_A01",
  verifier_assistant_id: "20261117_B02",
}

function button(wrapper: ReturnType<typeof mount>, text: string) {
  const found = wrapper.findAll("button").find((node) => node.text() === text)
  if (!found) throw new Error(`没有按钮：${text}`)
  return found
}

describe("工作流配置弹窗", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("新建时未填名称不发请求", async () => {
    const wrapper = mount(SopWorkflowEditor, { props: { cards } })
    await button(wrapper, "创建").trigger("click")
    await flushPromises()
    expect(wrapper.text()).toContain("给这条工作流起个名字")
    expect(createWorkflow).not.toHaveBeenCalled()
  })

  it("新建填完两侧名片后走 POST", async () => {
    const wrapper = mount(SopWorkflowEditor, { props: { cards } })
    await wrapper.find("input.assistant-input").setValue("桌面检查")
    const selects = wrapper.findAll("select")
    await selects[1].setValue("20261117_A01")
    await selects[2].setValue("20261117_B02")
    await button(wrapper, "创建").trigger("click")
    await flushPromises()
    expect(createWorkflow).toHaveBeenCalledWith({
      name: "桌面检查",
      orchestration: "sop",
      kind: "ui_automation",
      executor_assistant_id: "20261117_A01",
      verifier_assistant_id: "20261117_B02",
      leader_assistant_id: "",
      members: [],
    })
    expect(wrapper.emitted("saved")).toHaveLength(1)
    expect(updateWorkflow).not.toHaveBeenCalled()
  })

  it("编辑时预填当前绑定并走 PATCH", async () => {
    const wrapper = mount(SopWorkflowEditor, { props: { cards, workflow } })
    const input = wrapper.find("input.assistant-input")
    expect((input.element as HTMLInputElement).value).toBe("桌面检查")
    const selects = wrapper.findAll("select")
    expect((selects[0].element as HTMLSelectElement).disabled).toBe(true)
    expect((selects[1].element as HTMLSelectElement).value).toBe("20261117_A01")
    expect((selects[2].element as HTMLSelectElement).value).toBe("20261117_B02")

    await input.setValue("桌面检查（新）")
    await button(wrapper, "保存").trigger("click")
    await flushPromises()
    expect(updateWorkflow).toHaveBeenCalledWith(7, {
      name: "桌面检查（新）",
      orchestration: "sop",
      kind: "ui_automation",
      executor_assistant_id: "20261117_A01",
      verifier_assistant_id: "20261117_B02",
      leader_assistant_id: "",
      members: [],
    })
    expect(createWorkflow).not.toHaveBeenCalled()
    expect(wrapper.emitted("saved")).toHaveLength(1)
  })

  it("没有助手时提示先建助手且不能保存", async () => {
    const wrapper = mount(SopWorkflowEditor, { props: { cards: [] } })
    expect(wrapper.text()).toContain("先新建助手")
    expect(button(wrapper, "创建").attributes("disabled")).toBeDefined()
  })

  it("删除先二次确认，确认后才走 DELETE", async () => {
    const wrapper = mount(SopWorkflowEditor, { props: { cards, workflow } })
    await button(wrapper, "删除").trigger("click")
    await flushPromises()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(removeWorkflow).toHaveBeenCalledWith(7)
    expect(wrapper.emitted("deleted")).toHaveLength(1)
  })
})
