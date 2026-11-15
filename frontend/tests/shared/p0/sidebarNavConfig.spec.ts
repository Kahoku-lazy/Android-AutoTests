/**
 * [P0] 侧栏 AI任务 分组 — 任务清单入口与顺序
 */
import { describe, expect, it } from "vitest"
import { NAV_CATEGORIES, MOD_COLORS } from "@/shared/components/sidebarNavConfig"

describe("[P0] 侧栏 AI任务 导航", () => {
  it("顺序为 任务清单 / 用例管理 / 测试报告 / BUG单管理", () => {
    const group = NAV_CATEGORIES.find((category) => category.key === "ai-tasks")

    expect(group?.items.map((item) => item.label)).toEqual([
      "任务清单",
      "用例管理",
      "测试报告",
      "BUG单管理",
    ])
    expect(group?.items.map((item) => item.path)).toEqual(["/tasks", "/cases", "/reports", "/bugs"])
  })

  it("任务清单有独立模块色，避免与 AI 助手共用高亮", () => {
    expect(MOD_COLORS["/tasks"]).toBe("var(--c-ai)")
  })

  it("BUG单管理有独立模块色", () => {
    expect(MOD_COLORS["/bugs"]).toBe("var(--c-runner)")
  })
})

describe("[P0] 侧栏 AI 功能分组", () => {
  it("紧随仪表盘，AI 助手之后是执行报告（知识助手已下线）", () => {
    const keys = NAV_CATEGORIES.map((category) => category.key)
    expect(keys.slice(0, 2)).toEqual(["main", "ai"])

    const group = NAV_CATEGORIES.find((category) => category.key === "ai")
    expect(group?.label).toBe("AI 功能")
    expect(group?.items.map((item) => item.label)).toEqual(["AI 助手", "执行报告"])
    expect(group?.items.map((item) => item.path)).toEqual(["/ai-assistant", "/agent-reports"])
  })

  it("不再有知识库助手入口", () => {
    const paths = NAV_CATEGORIES.flatMap((category) => category.items.map((item) => item.path))
    expect(paths).not.toContain("/knowledge-assistant")
    expect(MOD_COLORS["/knowledge-assistant"]).toBeUndefined()
  })

  it("执行报告用报告模块色，不与 AI 助手共用高亮", () => {
    expect(MOD_COLORS["/agent-reports"]).toBe("var(--c-report)")
  })
})
