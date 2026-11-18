/**
 * [P0] 必测 — 自定义端口 CRUD 编排（spec: device-log-port-console 自定义端口登记 / 监听失败显式提示）
 * 目录：tests/serial-log/p0/
 *
 * 断言：新增失败 → 错误提示 + 刷新；成功 → 成功提示；重号短路不发请求；
 * 删除二次确认取消不发请求。
 */
import { ref } from "vue"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ElMessage, ElMessageBox } from "element-plus"
import type { LogPortRow } from "@/modules/serial-log/api"

const api = vi.hoisted(() => ({
  createLogPort: vi.fn(),
  updateLogPort: vi.fn(),
  deleteLogPort: vi.fn(),
}))

vi.mock("element-plus", () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))
vi.mock("@/modules/serial-log/api", () => api)

import { useCustomPorts } from "@/modules/serial-log/composables/useCustomPorts"

function makeRow(extra: Partial<LogPortRow> = {}): LogPortRow {
  return {
    port: 7008,
    sku: "H717D",
    baud: 115200,
    origin: "custom",
    address: "192.168.35.100:7008",
    enabled: true,
    listening: true,
    log_file: "H717D_7008.log",
    size_bytes: 0,
    note: "",
    ...extra,
  }
}

describe("[P0] useCustomPorts", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("新增成功且监听中 → 成功提示 + 刷新 + 关弹窗", async () => {
    api.createLogPort.mockResolvedValue({ status: true, data: makeRow() })
    const reload = vi.fn().mockResolvedValue(undefined)
    const ctrl = useCustomPorts(ref([]), reload)
    ctrl.openAdd()
    await ctrl.submit({ port: 7008, sku: "H717D", baud: 115200 })
    expect(api.createLogPort).toHaveBeenCalledWith({ port: 7008, sku: "H717D", baud: 115200 })
    expect(reload).toHaveBeenCalled()
    expect(ctrl.dialogVisible.value).toBe(false)
    expect(vi.mocked(ElMessage.success)).toHaveBeenCalled()
    expect(vi.mocked(ElMessage.error)).not.toHaveBeenCalled()
  })

  it("新增后监听失败 → 错误提示（不得显示成功）+ 刷新", async () => {
    api.createLogPort.mockResolvedValue({
      status: true,
      data: makeRow({ listening: false, note: "端口 7008 监听失败：端口已被其它程序占用" }),
    })
    const reload = vi.fn().mockResolvedValue(undefined)
    const ctrl = useCustomPorts(ref([]), reload)
    ctrl.openAdd()
    await ctrl.submit({ port: 7008, sku: "H717D", baud: 115200 })
    expect(vi.mocked(ElMessage.error)).toHaveBeenCalledWith(
      "端口 7008 监听失败：端口已被其它程序占用",
    )
    expect(vi.mocked(ElMessage.success)).not.toHaveBeenCalled()
    expect(reload).toHaveBeenCalled()
  })

  it("重号 → 表单错误短路，不发请求", async () => {
    const ctrl = useCustomPorts(ref([makeRow()]), vi.fn())
    ctrl.openAdd()
    await ctrl.submit({ port: 7008, sku: "X", baud: 9600 })
    expect(api.createLogPort).not.toHaveBeenCalled()
    expect(ctrl.formError.value).toContain("7008")
  })

  it("服务端 400 → 表单错误，弹窗不关", async () => {
    api.createLogPort.mockResolvedValue({ status: false, message: "端口必填且必须为数字" })
    const ctrl = useCustomPorts(ref([]), vi.fn())
    ctrl.openAdd()
    await ctrl.submit({ port: 7009, sku: "X", baud: 9600 })
    expect(ctrl.formError.value).toBe("端口必填且必须为数字")
    expect(ctrl.dialogVisible.value).toBe(true)
  })

  it("编辑走 updateLogPort 且不带端口号", async () => {
    api.updateLogPort.mockResolvedValue({ status: true, data: makeRow({ sku: "H717D-V2" }) })
    const ctrl = useCustomPorts(ref([makeRow()]), vi.fn().mockResolvedValue(undefined))
    ctrl.openEdit(makeRow())
    await ctrl.submit({ port: 7008, sku: "H717D-V2", baud: 115200 })
    expect(api.updateLogPort).toHaveBeenCalledWith(7008, { sku: "H717D-V2", baud: 115200 })
    expect(api.createLogPort).not.toHaveBeenCalled()
  })

  it("删除：确认后发请求并刷新；取消则不发", async () => {
    api.deleteLogPort.mockResolvedValue({
      status: true,
      data: { port: 7008, deleted: true, note: "已删除" },
    })
    const reload = vi.fn().mockResolvedValue(undefined)
    const ctrl = useCustomPorts(ref([makeRow()]), reload)
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce("confirm" as never)
    await ctrl.remove(makeRow())
    expect(api.deleteLogPort).toHaveBeenCalledWith(7008)
    expect(reload).toHaveBeenCalled()

    vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce("cancel")
    await ctrl.remove(makeRow())
    expect(api.deleteLogPort).toHaveBeenCalledTimes(1)
  })
})
