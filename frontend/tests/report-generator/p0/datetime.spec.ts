import { describe, expect, it } from "vitest"
import { formatReportTime } from "@/modules/report-generator/helpers/report-row"

describe("[P0] formatReportTime", () => {
  it("月-日 时:分", () => {
    expect(formatReportTime("2026-11-24T12:34:56")).toBe("11-24 12:34")
    expect(formatReportTime("2026-01-05T03:04:05")).toBe("01-05 03:04")
  })

  it("空串兜底为「—」，非法串原样返回", () => {
    expect(formatReportTime("")).toBe("—")
    expect(formatReportTime("not-a-time")).toBe("not-a-time")
  })
})
