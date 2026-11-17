import { flushPromises, mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"
import SopRunForm from "@/modules/ai-assistant/components/SopRunForm.vue"
import type { SopWorkflow } from "@/modules/ai-assistant/types"

const runWorkflow = vi.fn(async (_payload?: unknown) => ({ id: 42, status: "pending" }))

const devices = [
  { serial: "R5CT62RH88F", model: "SM-S9010", status: "ONLINE", connection_type: "USB" },
  {
    serial: "RF8N21MSW7A",
    connection_addr: "192.168.35.57:39569",
    model: "SM-G9730",
    status: "ONLINE",
    connection_type: "WIFI",
  },
  {
    serial: "RF8N21MSW7X",
    connection_addr: "adb-RF8N21MSW7X-abc._adb-tls-connect._tcp",
    status: "ONLINE",
    connection_type: "WIFI",
  },
]

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  runSopWorkflow: (payload: unknown) => runWorkflow(payload),
  listAutomationProjects: vi.fn(async () => [
    {
      id: 3,
      name: "自动化回归",
      rows: [
        { id: "TC-1", title: "打开首页" },
        { id: "TC-2", title: "进入设置页" },
      ],
    },
    { id: 4, name: "登录与权限", rows: [{ id: "TC-9", title: "账号被禁用后的提示" }] },
  ]),
}))

vi.mock("@/shared/api/devices", () => ({
  listDevices: vi.fn(async () => devices),
}))

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

function runButton(wrapper: ReturnType<typeof mount>) {
  return button(wrapper, "开始运行")
}

function deviceSelect(wrapper: ReturnType<typeof mount>) {
  const found = wrapper.findAll("select").find((node) => node.text().includes("请选择设备"))
  if (!found) throw new Error("没有设备下拉")
  return found
}

async function switchSource(wrapper: ReturnType<typeof mount>, label: string): Promise<void> {
  await button(wrapper, label).trigger("click")
}

async function pickYaml(wrapper: ReturnType<typeof mount>, name = "milestone.yaml"): Promise<File> {
  const file = new File(["name: 里程碑\nsteps: []"], name, { type: "text/yaml" })
  await switchSource(wrapper, "本地 YAML")
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, "files", { value: [file], configurable: true })
  await input.trigger("change")
  return file
}

async function pickCases(wrapper: ReturnType<typeof mount>, total = 1): Promise<void> {
  const boxes = wrapper.findAll('input[type="checkbox"]')
  for (let index = 0; index < total; index += 1) await boxes[index].setValue(true)
}

async function pickDevice(wrapper: ReturnType<typeof mount>): Promise<void> {
  await deviceSelect(wrapper).setValue("192.168.35.57:39569")
}

async function mountForm() {
  const wrapper = mount(SopRunForm, { props: { workflow } })
  await flushPromises()
  return wrapper
}

describe("工作流任务弹窗", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("平台来源没选用例时按钮不可用，并写明缺用例", async () => {
    const wrapper = await mountForm()
    expect(runButton(wrapper).attributes("disabled")).toBeDefined()
    expect(wrapper.text()).toContain("先选择自动化用例")
    expect(wrapper.text()).not.toContain("用例文件")
    await runButton(wrapper).trigger("click")
    await flushPromises()
    expect(runWorkflow).not.toHaveBeenCalled()
  })

  it("切到上传后没选 YAML 时按钮不可用，并写明缺 YAML", async () => {
    const wrapper = await mountForm()
    await switchSource(wrapper, "本地 YAML")
    expect(runButton(wrapper).attributes("disabled")).toBeDefined()
    expect(wrapper.text()).toContain("先上传一份里程碑 YAML")
    await runButton(wrapper).trigger("click")
    await flushPromises()
    expect(runWorkflow).not.toHaveBeenCalled()
  })

  it("设备是下拉选择，不能手填序列号", async () => {
    const wrapper = await mountForm()
    expect(deviceSelect(wrapper).exists()).toBe(true)
    expect(wrapper.find('.sop-run__side input[type="text"]').exists()).toBe(false)
    expect(wrapper.text()).toContain("请选择设备")
    expect(wrapper.text()).not.toContain("不指定设备")
  })

  it("下拉来自设备管理：USB 出序列号、局域网出 IP:端口，别名记录不列", async () => {
    const wrapper = await mountForm()
    const values = wrapper
      .findAll("option")
      .map((node) => (node.element as HTMLOptionElement).value)
    expect(values).toContain("R5CT62RH88F")
    expect(values).toContain("192.168.35.57:39569")
    expect(values.some((value) => value.includes("_adb-tls-connect._tcp"))).toBe(false)
    expect(wrapper.text()).toContain("192.168.35.57:39569 · SM-G9730")
  })

  it("用例来源是两段控件，切到本地 YAML 后不给平台用例面板", async () => {
    const wrapper = await mountForm()
    expect(wrapper.find(".case-picker").exists()).toBe(true)
    await switchSource(wrapper, "本地 YAML")
    expect(wrapper.find(".case-picker").exists()).toBe(false)
    expect(wrapper.find('input[type="file"]').exists()).toBe(true)
  })

  it("选用例与设备齐备后按钮可用，并写明已选条数", async () => {
    const wrapper = await mountForm()
    await pickCases(wrapper, 2)
    await pickDevice(wrapper)
    await flushPromises()
    expect(runButton(wrapper).attributes("disabled")).toBeUndefined()
    expect(wrapper.text()).toContain("已选 2 条用例")
  })

  it("摘要把跨项目的已选汇总成条数与项目数", async () => {
    const wrapper = await mountForm()
    await pickCases(wrapper, 3)
    await flushPromises()
    const summary = wrapper.find(".sop-run__summary").text()
    expect(summary).toContain("3 条")
    expect(summary).toContain("覆盖 2 个项目")
    expect(summary).toContain("打开首页")
  })

  it("切换用例来源会清空另一侧的已选", async () => {
    const wrapper = await mountForm()
    await pickCases(wrapper, 2)
    await switchSource(wrapper, "本地 YAML")
    await switchSource(wrapper, "平台用例")
    await flushPromises()
    expect(wrapper.find(".sop-run__summary").text()).toContain("0 条")
    expect(wrapper.findAll('input[type="checkbox"]:checked')).toHaveLength(0)
  })

  it("没选设备时按钮仍不可用", async () => {
    const wrapper = await mountForm()
    await pickYaml(wrapper)
    expect(runButton(wrapper).attributes("disabled")).toBeDefined()
    expect(wrapper.text()).toContain("先选择设备")
    expect(runWorkflow).not.toHaveBeenCalled()
  })

  it("选了设备就把它的可连地址带进请求", async () => {
    const wrapper = await mountForm()
    await pickYaml(wrapper)
    await pickDevice(wrapper)
    await flushPromises()
    await runButton(wrapper).trigger("click")
    await flushPromises()

    expect(runWorkflow).toHaveBeenCalledWith(
      expect.objectContaining({ serial: "192.168.35.57:39569" }),
    )
  })

  it("平台来源提交时带上已选用例编号，不带 YAML", async () => {
    const wrapper = await mountForm()
    await pickCases(wrapper, 2)
    await pickDevice(wrapper)
    await flushPromises()
    await runButton(wrapper).trigger("click")
    await flushPromises()

    expect(runWorkflow).toHaveBeenCalledWith(
      expect.objectContaining({ caseIds: ["TC-1", "TC-2"], yaml: null }),
    )
  })

  it("弹窗里写明当前工作流，不让用户再选一次", async () => {
    const wrapper = await mountForm()
    expect(wrapper.text()).toContain("工作流：桌面检查")
    expect(wrapper.text()).not.toContain("请选择工作流")
  })
})
