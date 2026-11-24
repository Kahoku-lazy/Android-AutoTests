import { beforeEach, describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import TaskResultPanel from "@/modules/dashboard/components/TaskResultPanel.vue"
import type { RecentTask } from "@/shared/types/dashboard"

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: pushMock }),
}))

const summary = { passed: 8, failed: 2 }

function mountPanel(props: { tasks?: RecentTask[]; summary?: typeof summary } = {}) {
  return mount(TaskResultPanel, {
    props: { summary, ...props },
  })
}

describe("[P1] TaskResultPanel", () => {
  beforeEach(() => {
    pushMock.mockClear()
  })

  it("摘要 chips：显示成功 / 失败", () => {
    const wrapper = mountPanel()
    const text = wrapper.find(".task-result-panel__summary").text()
    expect(text).toContain("8")
    expect(text).toContain("成功")
    expect(text).toContain("2")
    expect(text).toContain("失败")
  })

  it("任务为空：引导前往任务清单", () => {
    const wrapper = mountPanel({ tasks: [] })
    expect(wrapper.text()).toContain("暂无任务卡片，前往任务清单新建")
  })

  it("有用例文案才渲染副行", () => {
    const shown = mountPanel({
      tasks: [{ id: 12, status: "success", title: "工作流", case_label: "定时 · 共 2 条" }],
    })
    expect(shown.find(".task-row__case").text()).toBe("定时 · 共 2 条")

    const hidden = mountPanel({ tasks: [{ id: 13, status: "success", title: "旧任务" }] })
    expect(hidden.find(".task-row__case").exists()).toBe(false)
  })

  it("completed 映射为成功 ✓", () => {
    const wrapper = mountPanel({
      tasks: [{ id: 12, status: "completed", title: "助手卡" }],
    })
    const status = wrapper.find(".task-row__status")
    expect(status.text()).toBe("✓")
    expect(status.classes()).toContain("is-success")
  })

  it("有 id 时点击进入任务清单", async () => {
    const wrapper = mountPanel({
      tasks: [{ id: 12, status: "success", title: "已完成任务" }],
    })
    await wrapper.find(".task-row").trigger("click")
    expect(pushMock).toHaveBeenCalledWith("/tasks")
  })

  it("中断与取消不再显示成未执行", () => {
    const wrapper = mountPanel({
      tasks: [
        { id: 1, status: "interrupted", title: "中断" },
        { id: 2, status: "cancelled", title: "取消" },
      ],
    })
    const labels = wrapper.findAll(".task-row__status").map((node) => node.attributes("title"))
    expect(labels).toEqual(["已中断", "已取消"])
  })

  it("无任何 ID 的任务：点击不跳转", async () => {
    const wrapper = mountPanel({
      tasks: [{ status: "idle", title: "孤立任务" }],
    })
    await wrapper.find(".task-row").trigger("click")
    expect(pushMock).not.toHaveBeenCalled()
  })
})
