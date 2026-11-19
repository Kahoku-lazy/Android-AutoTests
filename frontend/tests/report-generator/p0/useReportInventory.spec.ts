/**
 * [P0] 报告台账列表：加载、来源筛选计数、关键字参数与错误态
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"
import * as reportApi from "@/modules/report-generator/api"
import { useReportInventory } from "@/modules/report-generator/composables/useReportInventory"
import { mountComposable } from "../../helpers/mountComposable"
import type { ReportListData } from "@/modules/report-generator/types"

vi.mock("@/modules/report-generator/api", () => ({
  listReports: vi.fn(),
}))

function payload(overrides: Partial<ReportListData> = {}): {
  data: { status: boolean; data: ReportListData }
} {
  return {
    data: {
      status: true,
      data: {
        summary: { total_reports: 5, sop_reports: 3, agent_reports: 2 },
        total: 5,
        items: [],
        ...overrides,
      },
    },
  }
}

describe("[P0] useReportInventory", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("load maps summary / total / items and tabs count reports", async () => {
    vi.mocked(reportApi.listReports).mockResolvedValue(payload())

    const { result, wrapper } = await mountComposable(() => useReportInventory())
    await flushPromises()

    expect(result.summary.value.total_reports).toBe(5)
    expect(result.total.value).toBe(5)
    expect(result.sourceTabs.value.map((tab) => tab.count)).toEqual([5, 3, 2])
    expect(result.error.value).toBe("")

    wrapper.unmount()
  })

  it("source filter is sent to the server and resets page", async () => {
    vi.mocked(reportApi.listReports).mockResolvedValue(payload())

    const { result, wrapper } = await mountComposable(() => useReportInventory())
    await flushPromises()

    result.source.value = "agent"
    await flushPromises()

    const calls = vi.mocked(reportApi.listReports).mock.calls
    const lastCall = calls[calls.length - 1]
    expect(lastCall?.[0]).toMatchObject({ source: "agent" })
    expect(result.currentPage.value).toBe(1)

    wrapper.unmount()
  })

  it("empty payload keeps zero counts and no error", async () => {
    vi.mocked(reportApi.listReports).mockResolvedValue(
      payload({ summary: { total_reports: 0, sop_reports: 0, agent_reports: 0 }, total: 0 }),
    )

    const { result, wrapper } = await mountComposable(() => useReportInventory())
    await flushPromises()

    expect(result.items.value).toEqual([])
    expect(result.sourceTabs.value.map((tab) => tab.count)).toEqual([0, 0, 0])
    expect(result.error.value).toBe("")

    wrapper.unmount()
  })

  it("failed load surfaces error for retry", async () => {
    vi.mocked(reportApi.listReports).mockRejectedValue(new Error("网络错误"))

    const { result, wrapper } = await mountComposable(() => useReportInventory())
    await flushPromises()

    expect(result.error.value).toBe("网络错误")
    expect(result.loading.value).toBe(false)

    wrapper.unmount()
  })
})
