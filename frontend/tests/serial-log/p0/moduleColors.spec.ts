import { describe, expect, it } from "vitest"
import {
  MODULE_COLOR_TOKENS,
  buildModuleColorMap,
  moduleColorOf,
} from "@/modules/serial-log/helpers/log-keyword-colors"

describe("[P0] 日志关键词模块色相", () => {
  it("按首次出现顺序取色：第一个模块拿第一枚令牌", () => {
    const map = buildModuleColorMap(["设备开关", "灯效库", "设备开关", "定时功能"])
    expect(map.get("设备开关")).toBe(MODULE_COLOR_TOKENS[0])
    expect(map.get("灯效库")).toBe(MODULE_COLOR_TOKENS[1])
    expect(map.get("定时功能")).toBe(MODULE_COLOR_TOKENS[2])
  })

  it("同一模块稳定同色；不同模块在色池容量内互不撞色", () => {
    const modules = ["设备开关", "灯效库", "颜色模式", "定时功能", "亮度", "音乐模式"]
    const map = buildModuleColorMap(modules)
    expect(new Set(modules.map((m) => map.get(m))).size).toBe(modules.length)
  })

  it("空模块只占一席；空串与空白视为同一模块", () => {
    const map = buildModuleColorMap(["", "  ", "亮度"])
    expect(map.get("")).toBe(MODULE_COLOR_TOKENS[0])
    expect(map.get("亮度")).toBe(MODULE_COLOR_TOKENS[1])
    expect(map.size).toBe(2)
  })

  it("色池用完才循环；未登记的模块回落到次级文字色", () => {
    const many = Array.from({ length: MODULE_COLOR_TOKENS.length + 1 }, (_, i) => `模块${i}`)
    const map = buildModuleColorMap(many)
    expect(map.get("模块0")).toBe(MODULE_COLOR_TOKENS[0])
    expect(map.get(many[MODULE_COLOR_TOKENS.length])).toBe(MODULE_COLOR_TOKENS[0])
    expect(moduleColorOf(map, "不存在的模块")).toBe("var(--app-text-secondary)")
  })
})
