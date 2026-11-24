/**
 * 本测试文件的业务功能如下：
 * 1. 锁住 shared/helpers/datetime.ts 的**当前**输出（golden）：相对时间四档 + 兜底、绝对时间到秒。
 * 2. 作为「时间格式化收口」的等价基准——实现换成共享入口后，本文件断言一字不改仍须全绿。
 *
 * Python 调试：本文件为前端用例，用 `npx vitest run tests/shared/p0/datetime.spec.ts` 单跑。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 shared/p0。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { formatDateTime, formatRelativeTime } from "@/shared/helpers/datetime"

describe("[P0] datetime golden", () => {
  beforeEach(() => {
    // 固定「现在」：2026-11-24 12:00:00 +08:00
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

    it("未来时刻按「刚刚」处理，不出现负值文案", () => {
      expect(formatRelativeTime("2026-11-24T12:05:00+08:00")).toBe("刚刚")
    })

    it("空串与非法串都兜底为「—」", () => {
      expect(formatRelativeTime("")).toBe("—")
      expect(formatRelativeTime("not-a-time")).toBe("—")
    })
  })

  describe("formatDateTime", () => {
    it("精确到秒，月日时分秒补零", () => {
      expect(formatDateTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34:56")
      expect(formatDateTime("2026-01-05T03:04:05")).toBe("2026-01-05 03:04:05")
    })

    it("接受后端「空格分隔」写法", () => {
      expect(formatDateTime("2026-11-24 12:34:56")).toBe("2026-11-24 12:34:56")
    })

    it("空串与非法串都兜底为「—」", () => {
      expect(formatDateTime("")).toBe("—")
      expect(formatDateTime("not-a-time")).toBe("—")
    })
  })
})
