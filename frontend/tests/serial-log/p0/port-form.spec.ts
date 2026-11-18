/**
 * [P0] 必测 — 新增 / 编辑端口表单纯校验（spec: device-log-port-console 自定义端口登记）
 * 目录：tests/serial-log/p0/
 *
 * 断言：重号 / 越界 / SKU 空 / 自定义波特率 / 编辑模式跳过端口校验。
 */
import { describe, expect, it } from "vitest"
import { validatePortForm } from "@/modules/serial-log/helpers/port-form"

const base = {
  portText: "7008",
  sku: "H717D",
  baudChoice: 921600 as number | "custom",
  baudCustomText: "",
}

describe("[P0] validatePortForm", () => {
  it("合法新增 → 输出 payload", () => {
    const check = validatePortForm(base, { editMode: false, existingPorts: [7005] })
    expect(check).toEqual({ kind: "ok", payload: { port: 7008, sku: "H717D", baud: 921600 } })
  })

  it("与已登记端口重号 → 拒绝", () => {
    const check = validatePortForm(base, { editMode: false, existingPorts: [7005, 7008] })
    expect(check.kind).toBe("error")
    if (check.kind === "error") expect(check.error).toContain("7008")
  })

  it.each(["0", "70000", "abc", ""])("端口非法（%s）→ 拒绝", (portText) => {
    const check = validatePortForm({ ...base, portText }, { editMode: false, existingPorts: [] })
    expect(check.kind).toBe("error")
  })

  it("SKU 为空 / 超 100 字符 → 拒绝", () => {
    expect(
      validatePortForm({ ...base, sku: "  " }, { editMode: false, existingPorts: [] }).kind,
    ).toBe("error")
    expect(
      validatePortForm({ ...base, sku: "x".repeat(101) }, { editMode: false, existingPorts: [] })
        .kind,
    ).toBe("error")
  })

  it("自定义波特率：正整数通过，非数字拒绝", () => {
    const ok = validatePortForm(
      { ...base, baudChoice: "custom", baudCustomText: "460800" },
      { editMode: false, existingPorts: [] },
    )
    expect(ok).toEqual({ kind: "ok", payload: { port: 7008, sku: "H717D", baud: 460800 } })
    const bad = validatePortForm(
      { ...base, baudChoice: "custom", baudCustomText: "abc" },
      { editMode: false, existingPorts: [] },
    )
    expect(bad.kind).toBe("error")
  })

  it("编辑模式：端口取 editPort，跳过重号与端口校验", () => {
    const check = validatePortForm(
      { ...base, portText: "abc" },
      { editMode: true, editPort: 7008, existingPorts: [7008] },
    )
    expect(check).toEqual({ kind: "ok", payload: { port: 7008, sku: "H717D", baud: 921600 } })
  })
})
