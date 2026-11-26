import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { formatDateTime, formatRelativeTime } from "@/modules/ops-console/helpers/datetime"

describe("[P0] ops-console datetime", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-11-24T12:00:00+08:00"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("近处与小时档", () => {
    expect(formatRelativeTime("2026-11-24T11:59:30+08:00")).toBe("刚刚")
    expect(formatRelativeTime("2026-11-24T11:55:00+08:00")).toBe("5 分钟前")
    expect(formatRelativeTime("2026-11-24T10:00:00+08:00")).toBe("2 小时前")
  })

  it("超过一天走天 / 月 / 年三档", () => {
    expect(formatRelativeTime("2026-11-21T12:00:00+08:00")).toBe("3 天前")
    expect(formatRelativeTime("2026-10-15T12:00:00+08:00")).toBe("1 个月前")
    expect(formatRelativeTime("2025-10-20T12:00:00+08:00")).toBe("1 年前")
  })

  it("空串与非法串兜底为「—」", () => {
    expect(formatRelativeTime("")).toBe("—")
    expect(formatRelativeTime("not-a-time")).toBe("—")
  })

  it("绝对时间只到分", () => {
    expect(formatDateTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34")
    expect(formatDateTime("")).toBe("—")
    expect(formatDateTime("not-a-time")).toBe("—")
  })
})
