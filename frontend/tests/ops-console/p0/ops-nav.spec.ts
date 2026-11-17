/**
 * [P0] 必测 — 运营入口的可见性与配色（spec: ops-user-console）
 *
 * 目录：tests/ops-console/p0/
 * 断言：① 侧栏存在「运营」分组且标记 requiresOperator；② 该分组排在最后（不插进既有顺序）；
 * ③ 入口路径与模块色已登记；④ 身份标签覆盖三种身份；⑤ 其余分组不受影响。
 */
import { describe, expect, it } from "vitest"
import { MOD_COLORS, NAV_CATEGORIES } from "@/shared/components/sidebarNavConfig"
import {
  OPS_GRANT_HINT,
  OPS_IDENTITY_LABELS,
  OPS_REVOKE_HINT,
  OPS_TABLE_COLUMNS,
} from "@/modules/ops-console/constants"

const OPS_PATH = "/ops/users"

describe("[P0] 侧栏运营入口", () => {
  it("存在「运营」分组且只有运营可见", () => {
    const ops = NAV_CATEGORIES.find((cat) => cat.key === "ops")
    expect(ops).toBeTruthy()
    expect(ops?.label).toBe("运营")
    expect(ops?.requiresOperator).toBe(true)
  })

  it("运营分组排在最后，不插进仪表盘与 AI 功能之间", () => {
    const keys = NAV_CATEGORIES.map((cat) => cat.key)
    expect(keys[keys.length - 1]).toBe("ops")
    expect(keys.indexOf("main")).toBeLessThan(keys.indexOf("ai"))
  })

  it("入口路径与模块色已登记", () => {
    const ops = NAV_CATEGORIES.find((cat) => cat.key === "ops")
    expect(ops?.items.map((item) => item.path)).toEqual([
      OPS_PATH,
      "/ops/agents",
      "/ops/model-configs",
    ])
    // 同分组内入口不得同色：用户管理 --c-account、Agent 配置 --c-element、模型配置 --c-ops
    expect(MOD_COLORS[OPS_PATH]).toBe("var(--c-account)")
    expect(MOD_COLORS["/ops/agents"]).toBe("var(--c-element)")
    expect(MOD_COLORS["/ops/model-configs"]).toBe("var(--c-ops)")
  })

  it("其余分组没有被标成运营专属", () => {
    const others = NAV_CATEGORIES.filter((cat) => cat.key !== "ops")
    expect(others.every((cat) => !cat.requiresOperator)).toBe(true)
  })
})

describe("[P0] 用户管理常量", () => {
  it("身份标签覆盖三种身份", () => {
    expect(Object.keys(OPS_IDENTITY_LABELS).sort()).toEqual(["operator", "superuser", "user"])
  })

  it("授予与取消各有一句确认文案", () => {
    expect(OPS_GRANT_HINT).toContain("运营后台")
    expect(OPS_REVOKE_HINT).toContain("失去运营入口")
  })

  it("表格列包含身份、状态与操作列", () => {
    const props = OPS_TABLE_COLUMNS.map((col) => col.prop)
    expect(props).toContain("identity")
    expect(props).toContain("is_active")
    expect(props).toContain("actions")
  })
})
