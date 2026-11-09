/**
 * [P0] 必测 — 任务发布表单：智能体必选、用例来源二选一、YAML 解析标题、提交载荷
 */
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"
import * as taskApi from "@/modules/task-list/api/tasks"
import * as agentApi from "@/modules/ai-assistant/api/agents"
import * as caseApi from "@/modules/case-manager/api"
import { useTaskPublish } from "@/modules/task-list/composables/useTaskPublish"
import { flattenFiles } from "@/modules/task-list/composables/usePlatformCases"
import { mountComposable } from "../../helpers/mountComposable"

vi.mock("@/modules/task-list/api/tasks", () => ({
  listDevices: vi.fn(),
  submitTask: vi.fn(),
}))

vi.mock("@/modules/ai-assistant/api/agents", () => ({
  listAgents: vi.fn(),
}))

vi.mock("@/modules/case-manager/api", () => ({
  listProjects: vi.fn(),
  getProjectTree: vi.fn(),
  getFileSheet: vi.fn(),
}))

const YAML_TEXT = `
- title: 甲
  steps:
    - action: a
      assert: b
- title: 乙
  steps:
    - action: c
      assert: d
`

function yamlFile(text = YAML_TEXT, name = "case.yaml"): File {
  return new File([text], name, { type: "text/yaml" })
}

function markdownFile(name = "prd.md"): File {
  return new File(["# 需求\n\n待机下单击 POWER 开机。"], name, { type: "text/markdown" })
}

describe("[P0] useTaskPublish", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.listDevices).mockResolvedValue({
      status: true,
      data: {
        devices: [
          { serial: "S1", model: "M1", status: "ONLINE", connection_type: "USB", last_seen: "" },
        ],
      },
    })
    vi.mocked(agentApi.listAgents).mockResolvedValue({
      status: true,
      data: {
        agents: [
          {
            id: 10,
            name: "自动化小助手",
            status: "active",
            task_kind: "device_control",
            route_configs: { device_control: { name: "Agent-01号" } },
          },
          {
            id: 11,
            name: "Agent-02",
            status: "active",
            task_kind: "case_authoring",
            route_configs: { case_authoring: { name: "Agent-02" } },
          },
        ],
      },
    })
    vi.mocked(caseApi.listProjects).mockResolvedValue({
      data: { status: true, data: [{ id: 7, name: "H6810 用例库" }] },
    } as never)
    vi.mocked(caseApi.getProjectTree).mockResolvedValue({
      data: {
        status: true,
        data: {
          project: { id: 7, name: "H6810 用例库" },
          tree: [
            {
              type: "directory",
              id: 1,
              name: "01",
              sort_order: 0,
              children: [{ type: "file", id: 21, name: "case", sort_order: 0, updated_at: "" }],
            },
            { type: "file", id: 20, name: "H6810_structured_cases", sort_order: 1, updated_at: "" },
          ],
        },
      },
    } as never)
    vi.mocked(caseApi.getFileSheet).mockResolvedValue({
      data: {
        status: true,
        data: {
          file: { id: 20, project_id: 7, directory_id: null, name: "H6810_structured_cases" },
          rows: [
            { id: "TC-1", title: "H6810 定时功能测试", step_count: 5 },
            { id: "TC-2", title: "H6810 颜色功能测试", step_count: 7 },
          ],
        },
      },
    } as never)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("智能体必选：未选时不可提交", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = "标题"
    result.form.value.device_serial = "S1"
    result.form.value.case_source = "yaml"
    await result.onConfigChange(yamlFile())
    expect(result.canSubmit()).toBe(false)

    result.form.value.agent_id = 10
    expect(result.canSubmit()).toBe(true)

    wrapper.unmount()
  })

  it("选 YAML 后解析出用例标题，换文件清空已选用例", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onConfigChange(yamlFile())
    expect(result.caseTitles.value).toEqual(["甲", "乙"])
    result.form.value.case_title = "乙"

    await result.onConfigChange(
      yamlFile("- title: 丙\n  steps:\n    - action: a\n      assert: b\n"),
    )
    expect(result.caseTitles.value).toEqual(["丙"])
    expect(result.form.value.case_title).toBe("")

    wrapper.unmount()
  })

  it("YAML 无法解析时给出可读错误且不生成选项", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onConfigChange(yamlFile("- steps: []\n"))
    expect(result.caseTitles.value).toEqual([])
    expect(result.caseError.value).toContain("title")

    wrapper.unmount()
  })

  it("本地 YAML 来源提交 title/agent_id/device_serial/case_source/case_title/config", async () => {
    vi.mocked(taskApi.submitTask).mockResolvedValue({
      status: true,
      data: { id: 1, status: "pending" },
    })
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = "校准"
    result.form.value.agent_id = 10
    result.form.value.device_serial = "S1"
    result.form.value.case_source = "yaml"
    await result.onConfigChange(yamlFile())
    result.form.value.case_title = "乙"
    await result.submit()
    await flushPromises()

    expect(taskApi.submitTask).toHaveBeenCalledTimes(1)
    const fd = vi.mocked(taskApi.submitTask).mock.calls[0][0] as FormData
    expect(fd.get("title")).toBe("校准")
    expect(fd.get("agent_id")).toBe("10")
    expect(fd.get("device_serial")).toBe("S1")
    expect(fd.get("case_source")).toBe("yaml")
    expect(fd.get("case_title")).toBe("乙")
    expect(fd.get("config")).toBeInstanceOf(File)
    expect(fd.get("case_ids")).toBeNull()
    expect(fd.get("goal")).toBeNull()
    expect(fd.get("documents")).toBeNull()

    wrapper.unmount()
  })

  it("平台用例来源：至少选一条才能提交，提交带 case_ids 且不带 config", async () => {
    vi.mocked(taskApi.submitTask).mockResolvedValue({
      status: true,
      data: { id: 3, status: "pending" },
    })
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = "H6810 回归"
    result.form.value.agent_id = 10
    result.form.value.device_serial = "S1"
    expect(result.form.value.case_source).toBe("platform")
    expect(result.canSubmit()).toBe(false)

    await result.onPlatformProjectChange(7)
    await flushPromises()
    expect(result.platform.files.value.map((f) => f.name)).toEqual([
      "case",
      "H6810_structured_cases",
    ])

    await result.onPlatformFileChange(20)
    await flushPromises()
    expect(result.platform.cases.value).toHaveLength(2)

    result.onPlatformCasesChange(["TC-1", "TC-2"])
    expect(result.canSubmit()).toBe(true)

    await result.submit()
    await flushPromises()

    const fd = vi.mocked(taskApi.submitTask).mock.calls[0][0] as FormData
    expect(fd.get("case_source")).toBe("platform")
    expect(JSON.parse(String(fd.get("case_ids")))).toEqual(["TC-1", "TC-2"])
    expect(fd.get("config")).toBeNull()
    expect(fd.get("case_title")).toBeNull()
    expect(fd.get("device_serial")).toBe("S1")

    wrapper.unmount()
  })

  it("切换用例来源清空另一侧已选内容", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onPlatformProjectChange(7)
    await result.onPlatformFileChange(20)
    await flushPromises()
    result.onPlatformCasesChange(["TC-1"])
    expect(result.form.value.caseIds).toEqual(["TC-1"])

    result.form.value.case_source = "yaml"
    await flushPromises()
    expect(result.form.value.caseIds).toEqual([])

    await result.onConfigChange(yamlFile())
    result.form.value.case_title = "甲"
    result.form.value.case_source = "platform"
    await flushPromises()
    expect(result.form.value.configFile).toBeNull()
    expect(result.form.value.case_title).toBe("")

    wrapper.unmount()
  })

  it("切项目或切表都会清空已选用例", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    await result.onPlatformProjectChange(7)
    await result.onPlatformFileChange(20)
    await flushPromises()
    result.onPlatformCasesChange(["TC-1", "TC-2"])

    await result.onPlatformFileChange(21)
    expect(result.form.value.caseIds).toEqual([])

    result.onPlatformCasesChange(["TC-1"])
    await result.onPlatformProjectChange(null)
    expect(result.form.value.caseIds).toEqual([])
    expect(result.platform.files.value).toEqual([])

    wrapper.unmount()
  })

  it("目录树拍平成用例表列表", () => {
    const files = flattenFiles([
      { type: "file", id: 1, name: "a", sort_order: 0, updated_at: "" },
      {
        type: "directory",
        id: 2,
        name: "01",
        sort_order: 1,
        children: [
          { type: "file", id: 3, name: "b", sort_order: 0, updated_at: "" },
          {
            type: "directory",
            id: 4,
            name: "02",
            sort_order: 1,
            children: [{ type: "file", id: 5, name: "c", sort_order: 0, updated_at: "" }],
          },
        ],
      },
    ])
    expect(files.map((item) => item.name)).toEqual(["a", "b", "c"])
  })

  it("Agent-02：上传 PRD/Word 后可提交，只带文档不带设备与 YAML", async () => {
    vi.mocked(taskApi.submitTask).mockResolvedValue({
      status: true,
      data: { id: 2, status: "pending" },
    })
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.title = "H717D 家电用例"
    result.form.value.agent_id = 11
    result.onDocumentChange({ raw: markdownFile("prd.md") } as never)
    result.onDocumentChange({ raw: markdownFile("需求补充.docx") } as never)

    expect(result.isCaseAuthoring.value).toBe(true)
    expect(result.canSubmit()).toBe(true)

    await result.submit()
    await flushPromises()

    const fd = vi.mocked(taskApi.submitTask).mock.calls[0][0] as FormData
    expect(fd.get("agent_id")).toBe("11")
    expect(fd.getAll("documents")).toHaveLength(2)
    expect(fd.get("device_serial")).toBeNull()
    expect(fd.get("config")).toBeNull()

    wrapper.unmount()
  })

  it("切到 Agent-02 会清掉设备任务字段，切回设备 Agent 会清掉文档", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()

    result.form.value.device_serial = "S1"
    result.form.value.case_title = "乙"
    result.form.value.agent_id = 11
    expect(result.form.value.device_serial).toBe("")
    expect(result.form.value.case_title).toBe("")

    result.onDocumentChange({ raw: markdownFile() } as never)
    expect(result.form.value.documents).toHaveLength(1)
    result.form.value.agent_id = 10
    expect(result.form.value.documents).toHaveLength(0)

    wrapper.unmount()
  })

  it("打开弹窗立即刷新设备，关闭后不再轮询", async () => {
    vi.useFakeTimers()
    const { result, wrapper } = await mountComposable(() => useTaskPublish())
    await flushPromises()
    const afterMount = vi.mocked(taskApi.listDevices).mock.calls.length

    result.openDialog()
    await flushPromises()
    expect(vi.mocked(taskApi.listDevices).mock.calls.length).toBe(afterMount + 1)

    vi.mocked(taskApi.listDevices).mockResolvedValue({
      status: true,
      data: {
        devices: [
          { serial: "S1", model: "M1", status: "ONLINE", connection_type: "USB", last_seen: "" },
          { serial: "S2", model: "M2", status: "ONLINE", connection_type: "USB", last_seen: "" },
        ],
      },
    })
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()
    expect(result.devices.value.some((d) => d.serial === "S2")).toBe(true)

    const afterPoll = vi.mocked(taskApi.listDevices).mock.calls.length
    result.closeDialog()
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()
    expect(vi.mocked(taskApi.listDevices).mock.calls.length).toBe(afterPoll)

    wrapper.unmount()
  })
})
