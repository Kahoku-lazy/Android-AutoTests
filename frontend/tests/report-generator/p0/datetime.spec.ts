/**
 * 本测试文件的业务功能如下：
 * 1. 锁住报告台账时间格式化的现口径：`MM-DD HH:mm`，非法串**原样返回**。
 *
 * Python 调试：本文件为前端用例，`npx vitest run tests/report-generator/p0/datetime.spec.ts`。
 * 时间：2026-11-24 创建（prune-frontend-dead-code 基线）。
 * 测试：`npm run test`；本文件属 report-generator/p0。
 */
import { describe, expect, it } from "vitest"

import { formatReportTime } from "@/modules/report-generator/helpers/report-row"

describe("[P0] formatReportTime 快照", () => {
  it("月-日 时:分", () => {
    expect(formatReportTime("2026-11-24T12:34:56")).toBe("11-24 12:34")
    expect(formatReportTime("2026-01-05T03:04:05")).toBe("01-05 03:04")
  })

  it("空串兜底为「—」，非法串原样返回", () => {
    expect(formatReportTime("")).toBe("—")
    expect(formatReportTime("not-a-time")).toBe("not-a-time")
  })
})
