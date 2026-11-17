import { describe, expect, it } from "vitest"
import {
  clockLabel,
  dayClockLabel,
  logCardTime,
  threadLogTime,
} from "@/modules/ai-assistant/helpers/time-label"

describe("对话页时间标签", () => {
  it("气泡时刻只取墙上时间，不换算时区", () => {
    expect(clockLabel("2026-11-16T17:55:30.123456+08:00")).toBe("17:55")
    expect(clockLabel("2026-11-16T17:55:30+08:00")).toBe("17:55")
  })

  it("空值与异常值不硬造时间", () => {
    expect(clockLabel("")).toBe("")
    expect(clockLabel("not-a-time")).toBe("")
  })

  it("日志卡跨日时间带月-日", () => {
    expect(dayClockLabel("2026-11-16T09:05:00+08:00")).toBe("11-16 09:05")
    expect(dayClockLabel("")).toBe("")
  })

  it("报告编号回落折成月-日 时:分，形态不符时原样返回", () => {
    expect(threadLogTime("20261116_175530")).toBe("11-16 17:55")
    expect(threadLogTime("legacy-run")).toBe("legacy-run")
    expect(threadLogTime("")).toBe("")
  })

  it("有消息时间就用消息时间，没有再回落编号", () => {
    expect(logCardTime("2026-11-16T17:55:30+08:00", "20260101_000000")).toBe("11-16 17:55")
    expect(logCardTime("", "20260101_080900")).toBe("01-01 08:09")
  })
})
