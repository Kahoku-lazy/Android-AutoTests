/**
 * 本测试文件的业务功能如下：
 * 1. 锁住任务卡时间格式化的现口径：**不解析 Date、不做时区换算**，只把 `T` 换成空格并截到分。
 *
 * Python 调试：本文件为前端用例，`npx vitest run tests/task-list/p0/datetime.spec.ts`。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 task-list/p0。
 */
import { describe, expect, it } from "vitest"

import { formatTaskTime } from "@/modules/task-list/helpers/task-detail"

describe("[P0] formatTaskTime 快照", () => {
  it("ISO 的 T 换空格并截到分", () => {
    expect(formatTaskTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34")
    expect(formatTaskTime("2026-11-24 12:34:56")).toBe("2026-11-24 12:34")
  })

  it("空值与空串返回空串（不是「—」）", () => {
    expect(formatTaskTime("")).toBe("")
    expect(formatTaskTime(undefined)).toBe("")
  })

  it("非法串按原样切片，不尝试解析", () => {
    expect(formatTaskTime("not-a-time")).toBe("not-a-time")
  })
})
