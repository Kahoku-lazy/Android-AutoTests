import { createApp, h, ref } from "vue"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ElMessage, ElMessageBox } from "element-plus"
import type { LogPortRow } from "@/modules/serial-log/api"

const api = vi.hoisted(() => ({
  fetchLogPorts: vi.fn(),
  toggleLogPort: vi.fn(),
  fetchLogPortLines: vi.fn(),
}))

vi.mock("element-plus", () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))
vi.mock("@/modules/serial-log/api", () => api)

import { useLogPorts } from "@/modules/serial-log/composables/useLogPorts"

function withSetup<T>(fn: () => T): T {
  let result!: T
  const app = createApp({
    setup() {
      result = fn()
      return () => h("div")
    },
  })
  app.mount(document.createElement("div"))
  return result
}

function makeRow(extra: Partial<LogPortRow> = {}): LogPortRow {
  return {
    port: 7005,
    sku: "H6810",
    baud: 921600,
    origin: "config",
    address: "192.168.35.100:7005",
    enabled: true,
    listening: true,
    log_file: "H6810_7005.log",
    size_bytes: 0,
    note: "",
    ...extra,
  }
}

describe("[P0] useLogPorts 失败提示与重试", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("loadPorts：listen_ip 入状态", async () => {
    api.fetchLogPorts.mockResolvedValue({
      status: true,
      data: { ports: [makeRow()], listen_ip: "192.168.35.100" },
    })
    const ctl = withSetup(() => useLogPorts())
    await ctl.loadPorts()
    expect(ctl.listenIp.value).toBe("192.168.35.100")
    expect(ctl.ports.value).toHaveLength(1)
  })

  it("开启但未监听 → 错误提示（不得 success），行状态更新", async () => {
    api.toggleLogPort.mockResolvedValue({
      status: true,
      data: makeRow({ listening: false, note: "端口 7005 监听失败：端口已被其它程序占用" }),
    })
    const ctl = withSetup(() => useLogPorts())
    const row = makeRow({ enabled: false, listening: false })
    await ctl.setEnabled(row, true)
    expect(vi.mocked(ElMessage.error)).toHaveBeenCalledWith(
      "端口 7005 监听失败：端口已被其它程序占用",
    )
    expect(vi.mocked(ElMessage.success)).not.toHaveBeenCalled()
    expect(row.listening).toBe(false)
    expect(row.note).toContain("监听失败")
  })

  it("开启且监听中 → 成功提示", async () => {
    api.toggleLogPort.mockResolvedValue({ status: true, data: makeRow() })
    const ctl = withSetup(() => useLogPorts())
    await ctl.setEnabled(makeRow({ enabled: false }), true)
    expect(vi.mocked(ElMessage.success)).toHaveBeenCalled()
    expect(vi.mocked(ElMessage.error)).not.toHaveBeenCalled()
  })

  it("重试 = 再次 toggle true", async () => {
    api.toggleLogPort.mockResolvedValue({ status: true, data: makeRow() })
    const ctl = withSetup(() => useLogPorts())
    const failed = makeRow({ listening: false, note: "端口 7005 监听失败：端口绑定失败" })
    await ctl.setEnabled(failed, true)
    expect(api.toggleLogPort).toHaveBeenCalledWith(7005, true)
    expect(failed.listening).toBe(true)
  })

  it("no_log 结论只给可读提示，不判监听失败", async () => {
    api.fetchLogPortLines.mockResolvedValue({
      status: true,
      data: {
        port: 7005,
        sku: "H6810",
        log_file: "H6810_7005.log",
        tail: 500,
        line_count: 0,
        raw_line_count: 0,
        lines: [],
        conclusion: "no_log",
        note: "暂无日志",
      },
    })
    const ctl = withSetup(() => useLogPorts())
    await ctl.openLog(makeRow())
    expect(ctl.conclusion.value).toBe("no_log")
    expect(vi.mocked(ElMessage.error)).not.toHaveBeenCalled()
    ctl.closeLog()
  })
})
