/**
 * 本测试文件的业务功能如下：
 * 1. 锁住运营台时间格式化的现口径：相对时间含「天 / 月 / 年」三档，绝对时间只到分。
 * 2. 作为收口后「薄包装」必须保持等价的基准。
 *
 * Python 调试：本文件为前端用例，`npx vitest run tests/ops-console/p0/datetime.spec.ts`。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 ops-console/p0。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { formatDateTime, formatRelativeTime } from "@/modules/ops-console/helpers/datetime"

describe("[P0] ops-console datetime 快照", () => {
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

  it("超过一天后走天 / 月 / 年三档（与共享默认档位不同）", () => {
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
