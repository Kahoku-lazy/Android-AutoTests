/**
 * [P0] 必测 — 任务统计：成功率口径、四类占比、统计随列表刷新
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"
import * as taskApi from "@/modules/task-list/api/tasks"
import { useTaskList } from "@/modules/task-list/composables/useTaskList"
import {
  hasOutcomeData,
  outcomeSlices,
  resultBarCards,
  successRateText,
} from "@/modules/task-list/helpers/task-stats"
import { mountComposable } from "../../helpers/mountComposable"
import type { TaskRecord, TaskStats } from "@/shared/types/ai"

vi.mock("@/modules/task-list/api/tasks", () => ({
  listTasks: vi.fn(),
  submitTask: vi.fn(),
  listDevices: vi.fn(),
  deleteTask: vi.fn(),
  clearTasks: vi.fn(),
  rerunTask: vi.fn(),
  getTaskStats: vi.fn(),
}))

function stats(overrides: Partial<TaskStats> = {}): TaskStats {
  return {
    total: 0,
    running: 0,
    pending: 0,
    success: 0,
    failed: 0,
    interrupted: 0,
    cancelled: 0,
    finished: 0,
    success_rate: 0,
    ...overrides,
  }
}

function makeTask(id: number): TaskRecord {
  return { id, title: `task-${id}`, goal: "", status: "completed" }
}

describe("successRateText", () => {
  it("没有数据或没有已结束任务时显示破折号", () => {
    expect(successRateText(null)).toBe("—")
    expect(successRateText(stats({ total: 2, pending: 2, finished: 0 }))).toBe("—")
  })

  it("整数百分比不补小数，非整数保留一位", () => {
    expect(successRateText(stats({ success: 9, finished: 10, success_rate: 90 }))).toBe("90%")
    expect(successRateText(stats({ success: 14, finished: 15, success_rate: 93.3 }))).toBe("93.3%")
  })
})

describe("outcomeSlices", () => {
  it("四类固定顺序并给出占比", () => {
    const slices = outcomeSlices(
      stats({ success: 7, failed: 2, interrupted: 1, cancelled: 0, total: 12, running: 2 }),
    )
    expect(slices.map((item) => item.label)).toEqual(["成功", "失败", "中断", "取消"])
    expect(slices.map((item) => item.percent)).toEqual([70, 20, 10, 0])
  })

  it("数量为 0 的类别仍保留在图例里", () => {
    const slices = outcomeSlices(stats({ success: 3 }))
    expect(slices).toHaveLength(4)
    expect(slices.find((item) => item.key === "cancelled")?.value).toBe(0)
  })

  it("四类全 0 时没有可画的数据", () => {
    expect(hasOutcomeData(stats({ total: 3, running: 1, pending: 2 }))).toBe(false)
    expect(hasOutcomeData(stats({ success: 1 }))).toBe(true)
  })

  it("空数据（null）也返回四类 0", () => {
    expect(outcomeSlices(null).map((item) => item.value)).toEqual([0, 0, 0, 0])
  })
})

describe("resultBarCards", () => {
  it("没有智能体时只有一张总体结果柱状图", () => {
    const cards = resultBarCards(stats({ total: 3, success: 3, finished: 3, success_rate: 100 }))
    expect(cards).toHaveLength(1)
    expect(cards[0].title).toBe("结果数量")
    expect(cards[0].caption).toBe("共 3 条 · 执行中 0 条")
    expect(cards[0].items.map((item) => item.value)).toEqual([3, 0, 0, 0])
  })

  it("每个可见智能体一张：标题用智能体名，含人数口径与成功率", () => {
    const cards = resultBarCards(
      stats({
        total: 5,
        success: 5,
        finished: 5,
        success_rate: 100,
        agents: [
          {
            ...stats({ total: 3, success: 2, failed: 1, finished: 3, success_rate: 66.7 }),
            id: 10,
            name: "Agent-01号",
          },
          {
            ...stats({ total: 2, success: 2, finished: 2, success_rate: 100 }),
            id: 617,
            name: "Agent-02",
          },
        ],
      }),
    )
    expect(cards.map((card) => card.key)).toEqual(["all", "agent-10", "agent-617"])
    expect(cards[1].title).toBe("Agent-01号")
    expect(cards[1].caption).toBe("共 3 条 · 执行中 0 · 成功率 66.7%")
    expect(cards[1].items.map((item) => item.value)).toEqual([2, 1, 0, 0])
  })

  it("新增智能体后自动多一张图（没有任务的给全 0）", () => {
    const cards = resultBarCards(
      stats({
        agents: [10, 11, 12].map((id) => ({
          ...stats({ total: 0 }),
          id,
          name: `Agent-${id}`,
        })),
      }),
    )
    expect(cards).toHaveLength(4)
    expect(cards[3].items.every((item) => item.value === 0)).toBe(true)
    expect(cards[3].caption).toContain("成功率 —")
  })
})

describe("useTaskList 统计", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2)] },
    })
    vi.mocked(taskApi.getTaskStats).mockResolvedValue({
      status: true,
      data: stats({ total: 12, running: 2, success: 9, failed: 1, finished: 10, success_rate: 90 }),
    })
  })

  it("load 成功后同时拿到统计", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.stats.value?.total).toBe(12)
    expect(successRateText(result.stats.value)).toBe("90%")

    wrapper.unmount()
  })

  it("删除任务后统计随之刷新", async () => {
    vi.mocked(taskApi.deleteTask).mockResolvedValue({ status: true })
    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()
    expect(taskApi.getTaskStats).toHaveBeenCalledTimes(1)

    vi.mocked(taskApi.getTaskStats).mockResolvedValue({
      status: true,
      data: stats({ total: 11, running: 2, success: 9, finished: 9, success_rate: 100 }),
    })
    await result.remove(result.tasks.value[0])
    await flushPromises()

    expect(taskApi.getTaskStats).toHaveBeenCalledTimes(2)
    expect(result.stats.value?.total).toBe(11)

    wrapper.unmount()
  })

  it("统计接口失败时保留上一次数值且不进入错误态", async () => {
    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()
    expect(result.stats.value?.total).toBe(12)

    vi.mocked(taskApi.getTaskStats).mockRejectedValue(new Error("boom"))
    vi.mocked(taskApi.listTasks).mockResolvedValue({ status: true, data: { tasks: [] } })
    await result.load()
    await flushPromises()

    expect(result.stats.value?.total).toBe(12)
    expect(result.error.value).toBe("")

    wrapper.unmount()
  })
})
