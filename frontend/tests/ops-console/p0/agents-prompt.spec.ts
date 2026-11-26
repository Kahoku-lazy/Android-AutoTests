import { mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"
import OpsPromptPreview from "@/modules/ops-console/components/OpsPromptPreview.vue"
import { OPS_AGENT_COLUMNS } from "@/modules/ops-console/constants"

const PROMPT = "## 角色\n你是验收角色。\n\n## 验收方法\n1. 判定主证据类型\n2. 调用 check_device_log"

const dialogStub = {
  template: "<div><slot /><slot name='footer' /></div>",
}

const writeText = vi.fn(async () => undefined)

beforeEach(() => {
  writeText.mockClear()
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText },
  })
})

describe("[P0] 系统提示词列的显示口径", () => {
  it("关掉 EP 溢出 tooltip，长文本改由「查看」弹窗承载", () => {
    const column = OPS_AGENT_COLUMNS.find((item) => item.prop === "system_prompt")
    expect(column).toBeDefined()
    expect(column?.showOverflowTooltip).toBe(false)
  })
})

describe("[P0] 系统提示词全文预览", () => {
  function mountPreview(prompt = PROMPT) {
    return mount(OpsPromptPreview, {
      props: { modelValue: true, name: "Android-UI-VERIFIER", prompt },
      global: { stubs: { "el-dialog": dialogStub } },
    })
  }

  it("原样渲染整份提示词，换行保真", () => {
    const wrapper = mountPreview()
    expect(wrapper.find(".ops-prompt-dialog__body").text()).toBe(PROMPT)
    expect(wrapper.text()).toContain("Android-UI-VERIFIER")
  })

  it("摘要给出字数与行数，便于判断是否是完整一份", () => {
    const wrapper = mountPreview()
    expect(wrapper.find(".ops-prompt-dialog__summary").text()).toBe(
      `${PROMPT.length} 字符 · ${PROMPT.split("\n").length} 行`,
    )
  })

  it("「复制全文」写入完整原文", async () => {
    const wrapper = mountPreview()
    await wrapper.find(".doodle-btn").trigger("click")
    await vi.waitFor(() => expect(writeText).toHaveBeenCalledWith(PROMPT))
    await vi.waitFor(() => expect(wrapper.text()).toContain("已复制"))
  })

  it("未填写时给出空态，复制键禁用", () => {
    const wrapper = mountPreview("")
    expect(wrapper.find(".ops-prompt-dialog__empty").exists()).toBe(true)
    expect(wrapper.find(".ops-prompt-dialog__body").exists()).toBe(false)
    expect(wrapper.find(".doodle-btn").attributes("disabled")).toBeDefined()
  })
})
