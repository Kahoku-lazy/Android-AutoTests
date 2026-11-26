import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"
import { nextTick } from "vue"
import ElementPlus from "element-plus"
import KeywordFormDialog from "@/modules/serial-log/components/KeywordFormDialog.vue"
import type { LogKeywordRow } from "@/modules/serial-log/helpers/log-keyword-rows"

const SCOPE_OPTIONS = [
  { value: "*", label: "通用" },
  { value: "H6601", label: "H6601专用" },
]

const EDIT_ROW: LogKeywordRow = {
  key: "switch_on|设备开关|0|打开设备成功|*",
  rowId: 5,
  keyword: "switch_on",
  module: "设备开关",
  featureId: 0,
  featureName: "打开设备成功",
  scope: "*",
}

async function mountDialog(editRow: LogKeywordRow | null = null) {
  const wrapper = mount(KeywordFormDialog, {
    props: { visible: false, editRow, scopeOptions: SCOPE_OPTIONS, saving: false, error: "" },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
  await wrapper.setProps({ visible: true })
  await nextTick()
  await nextTick()
  return wrapper
}

function inputs(wrapper: ReturnType<typeof mount>) {
  return wrapper.findAllComponents({ name: "ElInput" })
}

function clickSave(wrapper: ReturnType<typeof mount>): void {
  const buttons = wrapper.findAll(".kf-body button")
  const save = buttons.find((b) => b.text().includes("保存"))
  if (!save) throw new Error("save button not found")
  ;(save.element as HTMLElement).click()
}

describe("[P0] KeywordFormDialog", () => {
  it("新建打开清表单，范围默认通用", async () => {
    const wrapper = await mountDialog()
    const fields = inputs(wrapper)
    expect(fields[0].props("modelValue")).toBe("")
    expect(fields[1].props("modelValue")).toBe("")
    expect(fields[2].props("modelValue")).toBe("")
    expect(fields[3].props("modelValue")).toBe("")
    wrapper.unmount()
  })

  it("编辑打开回填行值", async () => {
    const wrapper = await mountDialog(EDIT_ROW)
    const fields = inputs(wrapper)
    expect(fields[0].props("modelValue")).toBe("switch_on")
    expect(fields[1].props("modelValue")).toBe("设备开关")
    expect(fields[2].props("modelValue")).toBe("打开设备成功")
    expect(fields[3].props("modelValue")).toBe("0")
    wrapper.unmount()
  })

  it("必填缺失本地拦截，不 emit submit", async () => {
    const wrapper = await mountDialog()
    clickSave(wrapper)
    await nextTick()
    expect(wrapper.emitted("submit")).toBeUndefined()
    expect(wrapper.find(".kf-err").text()).toContain("关键词必填")
    wrapper.unmount()
  })

  it("合法输入 emit 提交载荷", async () => {
    const wrapper = await mountDialog()
    const fields = inputs(wrapper)
    await fields[0].setValue("h6601_boot")
    await fields[1].setValue("设备开关")
    await fields[2].setValue("H6601开机完成")
    clickSave(wrapper)
    await nextTick()
    const emitted = wrapper.emitted("submit")
    expect(emitted).toBeTruthy()
    expect(emitted![0][0]).toEqual({
      keyword: "h6601_boot",
      module: "设备开关",
      feature: "H6601开机完成",
      scope: "*",
    })
    wrapper.unmount()
  })
})
