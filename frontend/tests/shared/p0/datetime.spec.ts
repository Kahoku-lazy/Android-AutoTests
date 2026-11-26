import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { formatDateTime, formatRelativeTime } from "@/shared/helpers/datetime"

describe("[P0] datetime golden", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-11-24T12:00:00+08:00"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe("formatRelativeTime", () => {
    it("30 秒前显示「刚刚」", () => {
      expect(formatRelativeTime("2026-11-24T11:59:30+08:00")).toBe("刚刚")
    })

    it("5 分钟前走分钟档", () => {
      expect(formatRelativeTime("2026-11-24T11:55:00+08:00")).toBe("5 分钟前")
    })

    it("2 小时前走小时档", () => {
      expect(formatRelativeTime("2026-11-24T10:00:00+08:00")).toBe("2 小时前")
    })

    it("超过一天回落本地日期", () => {
      expect(formatRelativeTime("2026-11-21T12:00:00+08:00")).toBe("2026/11/21")
    })

    it("未来时刻按「刚刚」处理", () => {
      expect(formatRelativeTime("2026-11-24T12:05:00+08:00")).toBe("刚刚")
    })

    it("空串与非法串兜底为「—」", () => {
      expect(formatRelativeTime("")).toBe("—")
      expect(formatRelativeTime("not-a-time")).toBe("—")
    })
  })

  describe("formatDateTime", () => {
    it("精确到秒且补零", () => {
      expect(formatDateTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34:56")
      expect(formatDateTime("2026-01-05T03:04:05")).toBe("2026-01-05 03:04:05")
    })

    it("接受空格分隔写法", () => {
      expect(formatDateTime("2026-11-24 12:34:56")).toBe("2026-11-24 12:34:56")
    })

    it("空串与非法串兜底为「—」", () => {
      expect(formatDateTime("")).toBe("—")
      expect(formatDateTime("not-a-time")).toBe("—")
    })
  })
})
