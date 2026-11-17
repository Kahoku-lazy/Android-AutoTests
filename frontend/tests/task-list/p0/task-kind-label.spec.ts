import { describe, expect, it } from "vitest"
import { taskKindLabel } from "@/modules/task-list/constants"
import { NAV_CATEGORIES } from "@/shared/components/sidebarNavConfig"

describe("任务卡类型与侧栏入口", () => {
  it("三类任务各有自己的文案", () => {
    expect(taskKindLabel("assistant_sop")).toBe("SOP")
    expect(taskKindLabel("case_authoring")).toBe("用例编写")
    expect(taskKindLabel("device_control")).toBe("设备执行")
  })

  it("AI任务第一项是已有任务清单", () => {
    const group = NAV_CATEGORIES.find((item) => item.key === "ai-tasks")
    expect(group?.items[0]).toMatchObject({ path: "/tasks", label: "任务清单" })
  })
})
