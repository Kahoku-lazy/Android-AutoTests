/**
 * 本测试文件的业务功能如下：
 * 1. 锁住 BUG 单时间格式化的现口径：到分，非法串**原样返回**（不改成「—」）。
 *
 * Python 调试：本文件为前端用例，`npx vitest run tests/bug-manager/p0/datetime.spec.ts`。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 bug-manager/p0。
 */
import { describe, expect, it } from "vitest"

import { formatBugTime } from "@/modules/bug-manager/constants"

describe("[P0] formatBugTime 快照", () => {
  it("精确到分", () => {
    expect(formatBugTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34")
    expect(formatBugTime("2026-01-05T03:04:05")).toBe("2026-01-05 03:04")
  })

  it("空串兜底为「—」，非法串原样返回", () => {
    expect(formatBugTime("")).toBe("—")
    expect(formatBugTime("not-a-time")).toBe("not-a-time")
  })
})
