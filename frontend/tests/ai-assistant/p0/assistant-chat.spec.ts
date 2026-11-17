import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import AssistantChat from "@/modules/ai-assistant/chat.vue"

const api = vi.hoisted(() => ({
  listThreads: vi.fn(async () => [
    { thread_id: "lane-1", status: "idle", title: "" },
    { thread_id: "lane-2", status: "done", title: "第二栏" },
  ]),
  createThread: vi.fn(),
  pollThread: vi.fn(async (threadId?: string) => ({
    status: "running",
    messages: [
      { role: "user", content: `你好 ${threadId}`, created_at: "2026-11-16T17:45:30+08:00" },
    ],
  })),
  sendThread: vi.fn(async () => undefined),
  cancelThread: vi.fn(async () => undefined),
  renameThread: vi.fn(async () => ({ thread_id: "lane-1", title: "" })),
  deleteThread: vi.fn(async () => undefined),
  listThreadLogs: vi.fn(async () => [
    { report_id: "", summary: "还在写", created_at: "", writing: true },
  ]),
  issueLogTicket: vi.fn(async () => "once"),
  threadLogUrl: (threadId: string, reportId: string, ticket = "") =>
    `/api/ai/assistants/threads/${threadId}/logs/${reportId}/${ticket ? `?ticket=${ticket}` : ""}`,
}))

vi.mock("vue-router", () => ({
  useRoute: () => ({
    params: { assistantId: "20261116_K3M" },
    query: { marker: "moss", name: "小助" },
  }),
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock("@/modules/ai-assistant/api/assistants", () => api)

/** 打开日志面板：点工具条上唯一那个「日志」按钮。 */
async function openLogs(wrapper: ReturnType<typeof mount>): Promise<void> {
  const button = wrapper.findAll("button").find((item) => item.text() === "日志")
  expect(button).toBeTruthy()
  await button!.trigger("click")
  await flushPromises()
}

describe("助手对话", () => {
  it("刷新后轮询到进行中的结果", async () => {
    vi.useFakeTimers()
    const wrapper = mount(AssistantChat)
    await flushPromises()
    expect(wrapper.text()).toContain("这一轮还在跑")
    expect(wrapper.text()).toContain("你好 lane-1")
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("每条气泡带自己的时刻", async () => {
    vi.useFakeTimers()
    api.pollThread.mockResolvedValueOnce({
      status: "done",
      messages: [
        { role: "user", content: "1+1=?", created_at: "2026-11-16T17:45:00+08:00" },
        { role: "assistant", content: "1+1=2。", created_at: "2026-11-16T17:46:12+08:00" },
      ],
    })
    const wrapper = mount(AssistantChat)
    await flushPromises()
    const times = wrapper.findAll(".ai-chat__time").map((item) => item.text())
    expect(times).toEqual(["17:45", "17:46"])
    expect(wrapper.find(".ai-chat__row--user .ai-chat__time").exists()).toBe(true)
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("左栏是带名称与笔色双波浪线的面板", async () => {
    vi.useFakeTimers()
    const wrapper = mount(AssistantChat)
    await flushPromises()
    expect(wrapper.find(".lane-panel").exists()).toBe(true)
    expect(wrapper.text()).toContain("对话栏")
    expect(wrapper.findAll(".lane-panel__wave")).toHaveLength(2)
    expect(wrapper.find(".lane-panel__lane.is-current").exists()).toBe(true)
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("日志卡住在左栏、不占网格格位，展开时只加宽左栏", async () => {
    vi.useFakeTimers()
    const wrapper = mount(AssistantChat)
    await flushPromises()

    const body = wrapper.find(".ai-chat__body")
    expect(body.classes()).not.toContain("is-logs-open")

    await openLogs(wrapper)

    expect(wrapper.find(".thread-log").exists()).toBe(true)
    expect(wrapper.find(".lane-column .thread-log").exists()).toBe(true)
    // 回归：日志曾是 .ai-chat__body 的第三个网格子项，会把对话区挤进 240px 左栏
    expect(wrapper.element.querySelectorAll(".ai-chat__body > *")).toHaveLength(2)
    expect(wrapper.find(".ai-chat__body > .thread-log").exists()).toBe(false)
    expect(wrapper.find(".ai-chat__pane .thread-log").exists()).toBe(false)
    expect(body.classes()).toContain("is-logs-open")
    expect(wrapper.text()).toContain("还在写")
    expect(wrapper.find(".thread-log__card").attributes("disabled")).toBeDefined()

    await wrapper.find(".thread-log__close").trigger("click")
    await flushPromises()
    expect(wrapper.find(".thread-log").exists()).toBe(false)
    expect(body.classes()).not.toContain("is-logs-open")
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("一轮日志是一张带胶带的卡，卡上有时间", async () => {
    vi.useFakeTimers()
    api.listThreadLogs.mockResolvedValueOnce([
      {
        report_id: "20261116_174500",
        summary: "1+1=2，直接回答",
        created_at: "2026-11-16T17:45:30+08:00",
        writing: false,
      },
      { report_id: "", summary: "还在写", created_at: "", writing: true },
    ])
    const wrapper = mount(AssistantChat)
    await flushPromises()
    await openLogs(wrapper)

    expect(wrapper.findAll(".thread-log__card")).toHaveLength(2)
    expect(wrapper.findAll(".thread-log__tape")).toHaveLength(2)
    const times = wrapper.findAll(".thread-log__time").map((item) => item.text())
    // 有消息时间用消息时间；进行中的一轮没有时间，给占位符
    expect(times).toEqual(["11-16 17:45", "—"])
    expect(wrapper.find(".thread-log__time").attributes("datetime")).toBe(
      "2026-11-16T17:45:30+08:00",
    )
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("本栏没有日志时给空态，取数失败给错误态并能重试", async () => {
    vi.useFakeTimers()
    api.listThreadLogs.mockResolvedValueOnce([])
    const wrapper = mount(AssistantChat)
    await flushPromises()

    await openLogs(wrapper)
    expect(wrapper.find(".thread-log .empty-state").exists()).toBe(true)
    expect(wrapper.find(".thread-log__card").exists()).toBe(false)

    api.listThreadLogs.mockRejectedValueOnce({ response: { status: 500 } })
    wrapper.find(".thread-log__close").trigger("click")
    await flushPromises()
    await openLogs(wrapper)
    expect(wrapper.find(".thread-log .error-state").exists()).toBe(true)

    api.listThreadLogs.mockResolvedValueOnce([
      { report_id: "20261116_120000", summary: "跑完一轮", created_at: "", writing: false },
    ])
    await wrapper.find(".error-state__btn").trigger("click")
    await flushPromises()
    expect(wrapper.text()).toContain("跑完一轮")
    // 老数据没有消息时间：回落报告编号里的时间戳
    expect(wrapper.find(".thread-log__time").text()).toBe("11-16 12:00")
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("切栏后日志跟着换栏取", async () => {
    vi.useFakeTimers()
    const wrapper = mount(AssistantChat)
    await flushPromises()

    await openLogs(wrapper)
    expect(api.listThreadLogs).toHaveBeenLastCalledWith("lane-1")

    await wrapper.find(".lane-panel__lane:nth-of-type(2) .lane-panel__open").trigger("click")
    await flushPromises()
    expect(api.listThreadLogs).toHaveBeenLastCalledWith("lane-2")
    wrapper.unmount()
    vi.useRealTimers()
  })

  it("一轮跑完后日志面板把「还在写」换成可打开的一条", async () => {
    vi.useFakeTimers()
    const wrapper = mount(AssistantChat)
    await flushPromises()
    await openLogs(wrapper)
    const callsBefore = api.listThreadLogs.mock.calls.length

    api.pollThread.mockResolvedValueOnce({ status: "done", messages: [] })
    api.listThreadLogs.mockResolvedValueOnce([
      {
        report_id: "20261116_180000",
        summary: "跑完一轮",
        created_at: "2026-11-16T18:00:05+08:00",
        writing: false,
      },
    ])
    await vi.advanceTimersByTimeAsync(2500)
    await flushPromises()

    expect(api.listThreadLogs.mock.calls.length).toBeGreaterThan(callsBefore)
    expect(wrapper.text()).toContain("跑完一轮")
    expect(wrapper.find(".thread-log__time").text()).toBe("11-16 18:00")
    expect(wrapper.find(".thread-log__card").attributes("disabled")).toBeUndefined()
    wrapper.unmount()
    vi.useRealTimers()
  })
})
