import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"
import ElementPlus from "element-plus"
import EvalCases from "@/modules/ai-assistant/eval-cases.vue"
import type { EvalCase } from "@/modules/ai-assistant/api/assistants"

const api = vi.hoisted(() => ({
  fetchEvalCases: vi.fn(),
  createEvalCase: vi.fn(),
  updateEvalCase: vi.fn(),
  deleteEvalCase: vi.fn(),
}))

vi.mock("@/modules/ai-assistant/api/assistants", () => api)
vi.mock("vue-router", () => ({ useRouter: () => ({ push: vi.fn() }) }))

function makeCase(id: number, title: string): EvalCase {
  return {
    id,
    title,
    note: "",
    enabled: true,
    steps: [{ action: "启动应用", assertion: "停在首页", anchor: { page: "首页" } }],
  }
}

function mountPage() {
  return mount(EvalCases, {
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

function bodyText(selector: string): string {
  return document.body.querySelector(selector)?.textContent?.trim() || ""
}

describe("评测题库页", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ""
    api.fetchEvalCases.mockResolvedValue([makeCase(1, "定时功能测试"), makeCase(2, "开关与亮度")])
    api.updateEvalCase.mockImplementation(async (id: number, payload: { title: string }) => ({
      ...makeCase(id, payload.title),
    }))
    api.createEvalCase.mockResolvedValue(makeCase(3, "新建题目"))
    api.deleteEvalCase.mockResolvedValue(undefined)
  })

  it("页顶不再有通栏动作按钮", async () => {
    const wrapper = mountPage()
    await flushPromises()
    const body = wrapper.find(".doc-body").element
    const buttons = Array.from(body.children).filter((node) => node.tagName === "BUTTON")
    expect(buttons).toHaveLength(0)
    wrapper.unmount()
  })

  it("表纸每行一题，行内给编辑与删除", async () => {
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.findAll(".bank-table__title").map((node) => node.text())).toEqual([
      "定时功能测试",
      "开关与亮度",
    ])
    const firstRowActions = wrapper.findAll(".bank-actions")[0]
    expect(firstRowActions.findAll("button").map((node) => node.text())).toEqual(["编辑", "删除"])
    wrapper.unmount()
  })

  it("编辑纸预填题目与步骤字段，取消不发写请求", async () => {
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.findAll(".bank-actions button")[0].trigger("click")
    await flushPromises()

    expect(bodyText(".el-dialog__title")).toContain("编辑题目")
    const inputs = Array.from(document.body.querySelectorAll(".bank-form__input")) as HTMLInputElement[]
    expect(inputs[0].value).toBe("定时功能测试")
    expect(inputs.map((input) => input.previousElementSibling?.textContent)).toEqual([
      "题目",
      "动作",
      "断言",
      "页面锚点",
    ])

    const buttons = Array.from(document.body.querySelectorAll(".el-dialog__footer button"))
    const cancel = buttons.find((node) => node.textContent?.includes("取消"))
    cancel?.dispatchEvent(new MouseEvent("click", { bubbles: true }))
    await flushPromises()

    expect(api.updateEvalCase).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it("保存只更新该行，不整页重载", async () => {
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.findAll(".bank-actions button")[0].trigger("click")
    await flushPromises()

    const titleInput = document.body.querySelector(".bank-form__input") as HTMLInputElement
    titleInput.value = "定时功能测试（改）"
    titleInput.dispatchEvent(new Event("input"))
    await flushPromises()

    const save = Array.from(document.body.querySelectorAll(".el-dialog__footer button")).find((node) =>
      node.textContent?.includes("保存"),
    )
    save?.dispatchEvent(new MouseEvent("click", { bubbles: true }))
    await flushPromises()

    expect(api.updateEvalCase).toHaveBeenCalledTimes(1)
    expect(api.fetchEvalCases).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll(".bank-table__title").map((node) => node.text())).toEqual([
      "定时功能测试（改）",
      "开关与亮度",
    ])
    wrapper.unmount()
  })

  it("空题库显示空态与新建入口", async () => {
    api.fetchEvalCases.mockResolvedValue([])
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.text()).toContain("还没有题目")
    expect(wrapper.text()).toContain("新建第一条")
    wrapper.unmount()
  })
})
