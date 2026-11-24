/**
 * 本测试文件的业务功能如下：
 * 1. 锁住 device-pool 时间格式化的**收口前**口径：相对时间到日期、绝对时间到秒。
 * 2. 其中「非法串」一例如实记录当前缺陷输出 `Invalid Date`——收口后该例改为「—」（见 4.6）。
 *
 * Python 调试：本文件为前端用例，`npx vitest run tests/device-pool/p0/datetime.spec.ts`。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 device-pool/p0。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { formatDateTime, formatRelativeTime } from "@/shared/helpers/datetime"

describe("[P0] device-pool datetime 快照", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-11-24T12:00:00+08:00"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("相对时间四档与设备池现口径一致", () => {
    expect(formatRelativeTime("2026-11-24T11:59:30+08:00")).toBe("刚刚")
    expect(formatRelativeTime("2026-11-24T11:55:00+08:00")).toBe("5 分钟前")
    expect(formatRelativeTime("2026-11-24T10:00:00+08:00")).toBe("2 小时前")
    expect(formatRelativeTime("2026-11-21T12:00:00+08:00")).toBe("2026/11/21")
  })

  it("空串兜底为「—」", () => {
    expect(formatRelativeTime("")).toBe("—")
  })

  it("[D5 唯一变化] 非法串兜底为「—」，不再漏出 Invalid Date", () => {
    // 收口前该例输出 "Invalid Date"（缺 NaN 判定）；收口后与全站其它 formatter 一致。
    // 这是本变更声明过的唯一可见变化，其余断言逐字未改。
    expect(formatRelativeTime("not-a-time")).toBe("—")
  })

  it("绝对时间到秒，空串与非法串兜底为「—」", () => {
    expect(formatDateTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34:56")
    expect(formatDateTime("")).toBe("—")
    expect(formatDateTime("not-a-time")).toBe("—")
  })
})
