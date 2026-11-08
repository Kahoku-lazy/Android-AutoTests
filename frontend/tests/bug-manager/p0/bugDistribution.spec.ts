/**
 * BUG 分布图表配置单测：summary → 图表数据的映射口径。
 */
import { describe, expect, it } from "vitest"
import {
  BUG_CATEGORY_BARS,
  BUG_STATUS_SLICES,
  buildDistributionOption,
  categorySeriesData,
  statusSeriesData,
} from "@/modules/bug-manager/helpers/bugDistribution"
import type { BugSummary } from "@/modules/bug-manager/types"

const SUMMARY: BugSummary = {
  total: 12,
  ui_automation: 5,
  case_authoring: 7,
  open: 4,
  resolved: 6,
  ignored: 2,
}

const ZERO: BugSummary = {
  total: 0,
  ui_automation: 0,
  case_authoring: 0,
  open: 0,
  resolved: 0,
  ignored: 0,
}

describe("statusSeriesData", () => {
  it("按 待处理/已解决/已忽略 顺序取 summary 数值", () => {
    const data = statusSeriesData(SUMMARY)
    expect(data.map((d) => d.name)).toEqual(["待处理", "已解决", "已忽略"])
    expect(data.map((d) => d.value)).toEqual([4, 6, 2])
    expect(BUG_STATUS_SLICES).toHaveLength(3)
  })

  it("全零时全部为 0", () => {
    expect(statusSeriesData(ZERO).map((d) => d.value)).toEqual([0, 0, 0])
  })
})

describe("categorySeriesData", () => {
  it("按 UI 自动化/用例编写 顺序取 summary 数值", () => {
    const data = categorySeriesData(SUMMARY)
    expect(data.map((d) => d.value)).toEqual([5, 7])
    expect(BUG_CATEGORY_BARS.map((bar) => bar.label)).toEqual(["UI 自动化", "用例编写"])
  })
})

describe("buildDistributionOption", () => {
  it("中心总数与 summary.total 一致", () => {
    const option = buildDistributionOption(SUMMARY)
    expect(option.graphic[0].style.text).toBe("12")
  })

  it("两个 series 与图例数据同源", () => {
    const option = buildDistributionOption(SUMMARY)
    expect(option.series).toHaveLength(2)
    expect(option.series[0].data).toEqual(statusSeriesData(SUMMARY))
    expect(option.series[1].data).toEqual(categorySeriesData(SUMMARY))
  })
})
