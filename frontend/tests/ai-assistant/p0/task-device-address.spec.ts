import { describe, expect, it } from "vitest"

import {
  isSelectableTaskDevice,
  taskDeviceAddress,
  taskDeviceLabel,
} from "@/modules/ai-assistant/helpers/task-device-address"

describe("[P0] taskDeviceAddress", () => {
  it("USB 提交序列号", () => {
    const device = { serial: "R5CT62RH88F", model: "SM-S9010", status: "ONLINE" }
    expect(taskDeviceAddress(device)).toBe("R5CT62RH88F")
    expect(taskDeviceLabel(device)).toBe("R5CT62RH88F · SM-S9010 (ONLINE)")
  })

  it("局域网提交 IP 与端口，不用库内硬件序列号", () => {
    const device = {
      serial: "RF8N21MSW7A",
      connection_addr: "192.168.35.57:39569",
      model: "SM-G9730",
      status: "ONLINE",
    }
    expect(taskDeviceAddress(device)).toBe("192.168.35.57:39569")
    expect(isSelectableTaskDevice(device)).toBe(true)
  })

  it("无线调试别名不可选", () => {
    const device = {
      serial: "RF8N21MSW7A",
      connection_addr: "adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp",
    }
    expect(isSelectableTaskDevice(device)).toBe(false)
  })
})
