import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"

const mocks = vi.hoisted(() => ({
  getTaskMedia: vi.fn(),
  createTaskMediaLink: vi.fn(),
}))

vi.mock("@/modules/task-list/api/tasks", () => ({
  getTaskMedia: mocks.getTaskMedia,
  createTaskMediaLink: mocks.createTaskMediaLink,
}))

import TaskMediaThumb from "@/modules/task-list/components/TaskMediaThumb.vue"

function mountThumb() {
  return mount(TaskMediaThumb, { props: { taskId: 5, mediaId: 9 } })
}

describe("TaskMediaThumb 新标签打开", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    if (!URL.createObjectURL) {
      Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:mock") })
    }
    if (!URL.revokeObjectURL) {
      Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn() })
    }
    mocks.getTaskMedia.mockResolvedValue(new Blob(["x"], { type: "image/webp" }))
  })

  it("签发直链后在新窗口打开", async () => {
    const win = { location: { href: "" }, close: vi.fn() }
    const openSpy = vi.spyOn(window, "open").mockReturnValue(win as unknown as Window)
    mocks.createTaskMediaLink.mockResolvedValue({
      status: true,
      data: { url: "/media/signed/5/9/1790000000/abc/", expires: 1790000000, expires_at: "" },
    })

    const wrapper = mountThumb()
    await flushPromises()

    const button = wrapper.get("button")
    expect(button.text()).toContain("在新标签打开")
    await button.trigger("click")
    await flushPromises()

    expect(openSpy).toHaveBeenCalledWith("", "_blank")
    expect(mocks.createTaskMediaLink).toHaveBeenCalledWith(5, 9)
    expect(win.location.href).toContain("/media/signed/5/9/1790000000/abc/")
  })

  it("签发失败时关闭空窗口", async () => {
    const win = { location: { href: "" }, close: vi.fn() }
    vi.spyOn(window, "open").mockReturnValue(win as unknown as Window)
    mocks.createTaskMediaLink.mockRejectedValue(new Error("denied"))

    const wrapper = mountThumb()
    await flushPromises()
    await wrapper.get("button").trigger("click")
    await flushPromises()

    expect(win.close).toHaveBeenCalled()
    expect(win.location.href).toBe("")
  })
})
