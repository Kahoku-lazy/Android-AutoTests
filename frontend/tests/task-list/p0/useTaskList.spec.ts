/**
 * [P0] 必测 — 任务列表加载、按状态分组、删除与清空
 * 目录：tests/ai-assistant/p0/
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"
import * as taskApi from "@/modules/task-list/api/tasks"
import { useTaskList } from "@/modules/task-list/composables/useTaskList"
import { mountComposable } from "../../helpers/mountComposable"
import type { TaskRecord } from "@/shared/types/ai"

vi.mock("@/modules/task-list/api/tasks", () => ({
  listTasks: vi.fn(),
  submitTask: vi.fn(),
  listDevices: vi.fn(),
  deleteTask: vi.fn(),
  clearTasks: vi.fn(),
  rerunTask: vi.fn(),
  getTaskStats: vi.fn(),
}))

function makeTask(id: number): TaskRecord {
  return {
    id,
    title: `task-${id}`,
    goal: `goal-${id}`,
    status: "completed",
  }
}

describe("[P0] useTaskList", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(taskApi.getTaskStats).mockResolvedValue({
      status: true,
      data: {
        total: 0,
        running: 0,
        pending: 0,
        success: 0,
        failed: 0,
        interrupted: 0,
        cancelled: 0,
        finished: 0,
        success_rate: 0,
      },
    })
  })

  it("load 成功后默认「全部任务」", async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2), makeTask(3)] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.tasks.value).toHaveLength(3)
    expect(result.activeFilter.value).toBe("all")
    expect(result.filteredItems.value).toHaveLength(3)

    wrapper.unmount()
  })

  it("列表为空时 emptyCopy 引导新建", async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [] },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.filteredItems.value).toHaveLength(0)
    expect(result.emptyCopy.value.text).toBe("还没有工作流任务")
    expect(result.emptyCopy.value.hint).not.toContain("新建任务")

    wrapper.unmount()
  })

  it("filteredItems 按状态分组合并 completed/success，空组不出现", async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: {
        tasks: [
          { ...makeTask(1), status: "pending" },
          { ...makeTask(2), status: "completed" },
          { ...makeTask(3), status: "success" },
          { ...makeTask(4), status: "failed" },
        ],
      },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    expect(result.groupedByStatus.value.map((g: { key: string }) => g.key)).toEqual([
      "pending",
      "success",
      "failed",
    ])
    const successGroup = result.groupedByStatus.value.find(
      (g: { key: string }) => g.key === "success",
    )
    expect(successGroup?.items).toHaveLength(2)

    wrapper.unmount()
  })

  it("只剩已中断时不再按运行态轮询", async () => {
    vi.useFakeTimers()
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [{ ...makeTask(1), status: "interrupted" }] },
    })

    const { wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()
    const calls = vi.mocked(taskApi.listTasks).mock.calls.length
    await vi.advanceTimersByTimeAsync(20_000)

    expect(vi.mocked(taskApi.listTasks).mock.calls.length).toBe(calls)
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("remove 成功后从列表去掉该任务", async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2)] },
    })
    vi.mocked(taskApi.deleteTask).mockResolvedValue({ status: true })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    await result.remove(result.tasks.value[0])
    await flushPromises()

    expect(taskApi.deleteTask).toHaveBeenCalledWith(1)
    expect(result.tasks.value.map((t: TaskRecord) => t.id)).toEqual([2])

    wrapper.unmount()
  })

  it("clearAll 成功后列表为空", async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [makeTask(1), makeTask(2)] },
    })
    vi.mocked(taskApi.clearTasks).mockResolvedValue({ status: true, data: { deleted: 2 } })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    await result.clearAll()
    await flushPromises()

    expect(taskApi.clearTasks).toHaveBeenCalled()
    expect(result.tasks.value).toHaveLength(0)

    wrapper.unmount()
  })

  it("rerun 已结束任务：失败、成功、取消都调用 API；执行中不调用", async () => {
    const failed = { ...makeTask(1), status: "failed", assistant_name: "UI 视觉自动化" }
    const ok = { ...makeTask(2), status: "completed", assistant_name: "UI 视觉自动化" }
    const cancelled = { ...makeTask(4), status: "cancelled", assistant_name: "UI 视觉自动化" }
    const running = { ...makeTask(5), status: "running", assistant_name: "UI 视觉自动化" }
    const refreshed = {
      status: true,
      data: {
        tasks: [
          failed,
          ok,
          cancelled,
          running,
          { ...makeTask(3), status: "pending", assistant_name: "UI 视觉自动化" },
        ],
      },
    }
    vi.mocked(taskApi.listTasks)
      .mockResolvedValueOnce({ status: true, data: { tasks: [failed, ok, cancelled, running] } })
      .mockResolvedValueOnce(refreshed)
      .mockResolvedValueOnce(refreshed)
      .mockResolvedValueOnce(refreshed)
    vi.mocked(taskApi.rerunTask).mockResolvedValue({
      status: true,
      data: { id: 3, status: "pending" },
    })

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()

    await result.rerun(running)
    await flushPromises()
    expect(taskApi.rerunTask).not.toHaveBeenCalled()

    await result.rerun(failed)
    await flushPromises()
    expect(taskApi.rerunTask).toHaveBeenCalledWith(1)

    await result.rerun(ok)
    await flushPromises()
    expect(taskApi.rerunTask).toHaveBeenCalledWith(2)

    await result.rerun(cancelled)
    await flushPromises()
    expect(taskApi.rerunTask).toHaveBeenCalledWith(4)
    expect(result.tasks.value).toHaveLength(5)
    expect(result.tasks.value.every((t: TaskRecord) => t.assistant_name === "UI 视觉自动化")).toBe(
      true,
    )

    wrapper.unmount()
  })

  it("轮询：上一轮未返回时跳过本轮，间隔 10 秒", async () => {
    vi.useFakeTimers()
    type ListResult = Awaited<ReturnType<typeof taskApi.listTasks>>
    let release: ((value: ListResult) => void) | null = null
    const running = { ...makeTask(1), status: "running" }
    const pending = new Promise<ListResult>((resolve) => {
      release = resolve
    })
    vi.mocked(taskApi.listTasks)
      .mockResolvedValueOnce({ status: true, data: { tasks: [running] } })
      .mockImplementationOnce(() => pending)

    const { result, wrapper } = await mountComposable(() => useTaskList())
    await flushPromises()
    expect(result.tasks.value[0].status).toBe("running")

    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(2)

    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(2)

    release?.({ status: true, data: { tasks: [running] } } as ListResult)
    await flushPromises()
    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(3)

    wrapper.unmount()
    vi.useRealTimers()
  })

  it("离开清单（keep-alive 失活）后不再轮询，回到清单静默补拉一次", async () => {
    vi.useFakeTimers()
    const running = { ...makeTask(1), status: "running" }
    vi.mocked(taskApi.listTasks).mockResolvedValue({
      status: true,
      data: { tasks: [running] },
    })

    const { deactivate, activate, wrapper } = await mountComposable(() => useTaskList(), {
      keepAlive: true,
    })
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(1)

    // keep-alive 缓存：只失活，不卸载
    await deactivate?.()
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(1)

    await activate?.()
    await flushPromises()
    expect(taskApi.listTasks).toHaveBeenCalledTimes(2)

    wrapper.unmount()
    vi.useRealTimers()
  })
})
