import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { formatDateTime, formatRelativeTime } from "@/shared/helpers/datetime"

describe("[P0] device-pool datetime", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-11-24T12:00:00+08:00"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("相对时间四档", () => {
    expect(formatRelativeTime("2026-11-24T11:59:30+08:00")).toBe("刚刚")
    expect(formatRelativeTime("2026-11-24T11:55:00+08:00")).toBe("5 分钟前")
    expect(formatRelativeTime("2026-11-24T10:00:00+08:00")).toBe("2 小时前")
    expect(formatRelativeTime("2026-11-21T12:00:00+08:00")).toBe("2026/11/21")
  })

  it("空串兜底为「—」", () => {
    expect(formatRelativeTime("")).toBe("—")
  })

  it("收口后非法串兜底为「—」，不再漏出 Invalid Date", () => {
    expect(formatRelativeTime("not-a-time")).toBe("—")
  })

  it("绝对时间到秒，空串与非法串兜底为「—」", () => {
    expect(formatDateTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34:56")
    expect(formatDateTime("")).toBe("—")
    expect(formatDateTime("not-a-time")).toBe("—")
  })
})
