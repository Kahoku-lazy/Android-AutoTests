import { describe, expect, it } from "vitest"
import { formatBugTime } from "@/modules/bug-manager/constants"

describe("[P0] formatBugTime", () => {
  it("精确到分", () => {
    expect(formatBugTime("2026-11-24T12:34:56")).toBe("2026-11-24 12:34")
    expect(formatBugTime("2026-01-05T03:04:05")).toBe("2026-01-05 03:04")
  })

  it("空串兜底为「—」，非法串原样返回", () => {
    expect(formatBugTime("")).toBe("—")
    expect(formatBugTime("not-a-time")).toBe("not-a-time")
  })
})
