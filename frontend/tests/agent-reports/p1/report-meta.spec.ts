/**
 * 执行报告模块纯函数 — 字节格式化、相对时间、微倾轮转、运行名拆时间
 */
import { describe, expect, it } from "vitest"

import {
  formatBytes,
  formatRunTime,
  runStamp,
  tiltFor,
} from "@/modules/agent-reports/helpers/report-meta"
import { REPORTS_TILT_STEPS } from "@/modules/agent-reports/constants"

describe("[P1] formatBytes", () => {
  it("按 1024 进制逐级换算并保留一位小数", () => {
    expect(formatBytes(0)).toBe("0 B")
    expect(formatBytes(512)).toBe("512 B")
    expect(formatBytes(33_162)).toBe("32.4 KB")
    expect(formatBytes(103_873)).toBe("101.4 KB")
  })

  it("非法输入返回占位符", () => {
    expect(formatBytes(-1)).toBe("—")
    expect(formatBytes(Number.NaN)).toBe("—")
  })
})

describe("[P1] formatRunTime", () => {
  it("按距今时长给相对时间", () => {
    const now = Date.now()
    expect(formatRunTime(Math.floor(now / 1000))).toBe("刚刚")
    expect(formatRunTime(Math.floor((now - 5 * 60_000) / 1000))).toBe("5 分钟前")
    expect(formatRunTime(Math.floor((now - 3 * 3_600_000) / 1000))).toBe("3 小时前")
    expect(formatRunTime(Math.floor((now - 2 * 86_400_000) / 1000))).toBe("2 天前")
  })

  it("非法输入返回占位符", () => {
    expect(formatRunTime(0)).toBe("—")
    expect(formatRunTime(Number.NaN)).toBe("—")
  })
})

describe("[P1] tiltFor", () => {
  it("按序号轮转，且能处理越界下标", () => {
    expect(tiltFor(0)).toBe(REPORTS_TILT_STEPS[0])
    expect(tiltFor(REPORTS_TILT_STEPS.length)).toBe(REPORTS_TILT_STEPS[0])
    expect(tiltFor(1)).not.toBe(tiltFor(0))
  })
})

describe("[P1] runStamp", () => {
  it("把运行目录名拆成可读时间", () => {
    expect(runStamp("20261114_200839_ui_executor")).toBe("2026-11-14 20:08:39")
  })

  it("不符合约定时原样返回", () => {
    expect(runStamp("weird-name")).toBe("weird-name")
  })
})
