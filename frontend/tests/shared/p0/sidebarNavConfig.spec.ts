import { describe, expect, it } from "vitest"
import { NAV_CATEGORIES, MOD_COLORS } from "@/shared/components/sidebarNavConfig"
import { lucideIconSubset } from "@/shared/icons/lucide-registry"

function toIconKey(name: string): string {
  return name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("")
}

describe("[P0] 侧栏 AI任务 导航", () => {
  it("顺序为 任务清单 / 用例管理 / BUG单管理 / 测试报告", () => {
    const group = NAV_CATEGORIES.find((category) => category.key === "ai-tasks")

    expect(group?.items.map((item) => item.label)).toEqual([
      "任务清单",
      "用例管理",
      "BUG单管理",
      "测试报告",
    ])
    expect(group?.items.map((item) => item.path)).toEqual(["/tasks", "/cases", "/bugs", "/reports"])
  })

  it("任务清单有独立模块色，避免与 AI 助手共用高亮", () => {
    expect(MOD_COLORS["/tasks"]).toBe("var(--c-task)")
  })

  it("BUG单管理有独立模块色", () => {
    expect(MOD_COLORS["/bugs"]).toBe("var(--c-runner)")
  })

  it("测试报告排在 BUG单管理之后，且与同组三项不同色", () => {
    expect(MOD_COLORS["/reports"]).toBe("var(--c-report)")
    const groupColors = ["/tasks", "/cases", "/bugs", "/reports"].map((path) => MOD_COLORS[path])
    expect(new Set(groupColors).size).toBe(4)
  })
})

describe("[P0] 侧栏入口配色互不重复", () => {
  it("数据组的设备管理与串口日志不同色", () => {
    expect(MOD_COLORS["/devices"]).not.toBe(MOD_COLORS["/serial-log"])
  })

  it("数据组末尾有知识库入口，且与同组两项不同色", () => {
    const group = NAV_CATEGORIES.find((category) => category.key === "data")
    expect(group?.items.map((item) => item.path)).toEqual([
      "/devices",
      "/serial-log",
      "/knowledge-search",
    ])
    const dataColors = ["/devices", "/serial-log", "/knowledge-search"].map(
      (path) => MOD_COLORS[path],
    )
    expect(new Set(dataColors).size).toBe(3)
  })

  it("运营组三项互相不同色", () => {
    const ops = ["/ops/users", "/ops/agents", "/ops/model-configs"].map((path) => MOD_COLORS[path])
    expect(new Set(ops).size).toBe(3)
  })

  it("任务清单与 AI 助手不同色", () => {
    expect(MOD_COLORS["/tasks"]).not.toBe(MOD_COLORS["/ai-assistant"])
  })

  it("每个导航入口都有模块色", () => {
    const missing = NAV_CATEGORIES.flatMap((category) =>
      category.items.map((item) => item.path),
    ).filter((path) => !MOD_COLORS[path])
    expect(missing).toEqual([])
  })
})

describe("[P0] 侧栏图标登记", () => {
  it("每个导航图标都在 lucide 子集里登记（漏登记会让图标方块空着）", () => {
    const missing = NAV_CATEGORIES.flatMap((category) =>
      category.items.map((item) => item.icon),
    ).filter((icon) => !lucideIconSubset[toIconKey(icon)])
    expect(missing).toEqual([])
  })
})

describe("[P0] 侧栏 AI 功能分组", () => {
  it("紧随仪表盘，且不渲染分组标题", () => {
    const keys = NAV_CATEGORIES.map((category) => category.key)
    expect(keys.slice(0, 2)).toEqual(["main", "ai"])

    const group = NAV_CATEGORIES.find((category) => category.key === "ai")

    expect(group?.label).toBe("")
    expect(group?.items.map((item) => item.label)).toEqual(["平台助手"])
    expect(group?.items.map((item) => item.path)).toEqual(["/ai-assistant"])
  })

  it("不再有知识库助手入口", () => {
    const paths = NAV_CATEGORIES.flatMap((category) => category.items.map((item) => item.path))
    expect(paths).not.toContain("/knowledge-assistant")
    expect(MOD_COLORS["/knowledge-assistant"]).toBeUndefined()
  })

  it("测试报告用报告模块色，不与 AI 助手共用高亮", () => {
    expect(MOD_COLORS["/reports"]).toBe("var(--c-report)")
    expect(MOD_COLORS["/reports"]).not.toBe(MOD_COLORS["/ai-assistant"])
    expect(MOD_COLORS["/agent-reports"]).toBeUndefined()
  })
})
