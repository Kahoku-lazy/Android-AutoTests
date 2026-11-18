/**
 * [P0] 必测 — 日志关键词表格行与搜索 / 范围筛选（spec: device-log-keyword-catalog）
 *
 * 目录：tests/serial-log/p0/
 * 断言：① 表内顺序（关键词按表内先后、功能点按表内先后，前端不重排）；
 * ② 一个关键词对应多个功能点 → 多行；③ 计数口径（关键词去重、功能点按模块+编号+名称去重，范围不参与去重）；
 * ④ 搜索覆盖关键词 / 模块 / 功能点，清空回全量；⑤ 缺名占位不丢行；
 * ⑥ 范围：缺省按通用、行标识含范围、范围筛选与搜索叠加、选项派生通用恒首。
 */
import { describe, expect, it } from "vitest"
import {
  SCOPE_FILTER_ALL,
  SCOPE_GENERAL,
  UNNAMED_FEATURE,
  UNNAMED_MODULE,
  buildKeywordRows,
  filterKeywordRows,
  filterKeywordRowsByScope,
  keywordRowCounts,
  scopeLabel,
  scopeOptions,
  type LogKeywordScopedFeature,
} from "@/modules/serial-log/helpers/log-keyword-rows"
import type { LogKeywordEntry } from "@/modules/serial-log/api"

const ENTRIES: LogKeywordEntry[] = [
  { keyword: "switch_on", features: [{ id: 0, module: "设备开关", feature: "打开设备成功" }] },
  {
    keyword: "color_configs_set_success",
    features: [
      { id: 2, module: "音效律动", feature: "灯光颜色设置成功" },
      { id: 17, module: "彩色模式", feature: "手动-颜色设置成功" },
    ],
  },
  { keyword: "switch_off", features: [{ id: 1, module: "设备开关", feature: "关闭设备成功" }] },
]

describe("[P0] buildKeywordRows", () => {
  it("一行一个「关键词 × 功能点」，顺序与表内一致", () => {
    const rows = buildKeywordRows(ENTRIES)
    expect(rows.map((r) => [r.keyword, r.featureId])).toEqual([
      ["switch_on", 0],
      ["color_configs_set_success", 2],
      ["color_configs_set_success", 17],
      ["switch_off", 1],
    ])
    expect(rows[0]).toMatchObject({ module: "设备开关", featureName: "打开设备成功" })
  })

  it("行标识唯一（同关键词不同功能点不冲突）", () => {
    const keys = buildKeywordRows(ENTRIES).map((r) => r.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it("缺模块 / 缺功能点名给占位，不丢行", () => {
    const rows = buildKeywordRows([{ keyword: "x", features: [{ id: 1 }] }])
    expect(rows.length).toBe(1)
    expect(rows[0].module).toBe(UNNAMED_MODULE)
    expect(rows[0].featureName).toBe(UNNAMED_FEATURE)
  })

  it("关键词为空的条目跳过", () => {
    expect(buildKeywordRows([{ keyword: "  ", features: [{ id: 1 }] }])).toEqual([])
  })

  it("计数按去重口径：关键词去重、功能点按模块+编号+名称去重", () => {
    const counts = keywordRowCounts(buildKeywordRows(ENTRIES))
    expect(counts.keywords).toBe(3)
    expect(counts.features).toBe(4)
  })
})

describe("[P0] filterKeywordRows", () => {
  const rows = buildKeywordRows(ENTRIES)

  it("空查询返回全量", () => {
    expect(filterKeywordRows(rows, "   ")).toEqual(rows)
  })

  it("按关键词搜索（忽略大小写，多功能点的行都在）", () => {
    const hit = filterKeywordRows(rows, "COLOR_CONFIGS")
    expect(hit.length).toBe(2)
    expect(hit.map((r) => r.featureId)).toEqual([2, 17])
  })

  it("按功能点名搜索", () => {
    expect(filterKeywordRows(rows, "定时")).toEqual([])
    expect(filterKeywordRows(rows, "关闭设备").map((r) => r.keyword)).toEqual(["switch_off"])
  })

  it("按模块名搜索", () => {
    expect(filterKeywordRows(rows, "设备开关").length).toBe(2)
  })

  it("无命中返回空数组", () => {
    expect(filterKeywordRows(rows, "zzz-not-exist")).toEqual([])
  })
})

/** 带范围的条目构造器（api.ts 契约补 scope 前的过渡类型） */
function entry(keyword: string, features: LogKeywordScopedFeature[]): LogKeywordEntry {
  return { keyword, features }
}

const SCOPED_ENTRIES: LogKeywordEntry[] = [
  entry("switch_on", [{ id: 0, module: "设备开关", feature: "打开设备成功", scope: "*" }]),
  entry("h6601_boot", [{ id: 56, module: "设备开关", feature: "H6601开机完成", scope: "H6601" }]),
  entry("switch_off", [{ id: 1, module: "设备开关", feature: "关闭设备成功" }]),
  entry("h2234_boot", [{ id: 57, module: "设备开关", feature: "H2234开机完成", scope: "H2234" }]),
]

describe("[P0] 范围（scope）", () => {
  it("缺省范围按通用处理，行标识含范围", () => {
    const rows = buildKeywordRows(SCOPED_ENTRIES)
    expect(rows.map((r) => r.scope)).toEqual(["*", "H6601", "*", "H2234"])
    expect(new Set(rows.map((r) => r.key)).size).toBe(rows.length)
  })

  it("同关键词同功能点不同范围是两行，行标识不冲突", () => {
    const rows = buildKeywordRows([
      entry("switch_on", [
        { id: 0, module: "设备开关", feature: "打开设备成功", scope: "*" },
        { id: 0, module: "设备开关", feature: "打开设备成功", scope: "H6601" },
      ]),
    ])
    expect(rows.length).toBe(2)
    expect(new Set(rows.map((r) => r.key)).size).toBe(2)
  })

  it("范围展示口径：通用 / <SKU>专用", () => {
    expect(scopeLabel(SCOPE_GENERAL)).toBe("通用")
    expect(scopeLabel("H6601")).toBe("H6601专用")
  })

  it("范围筛选：全部 / 空值回全量，通用与各 SKU 精确匹配", () => {
    const rows = buildKeywordRows(SCOPED_ENTRIES)
    expect(filterKeywordRowsByScope(rows, SCOPE_FILTER_ALL)).toEqual(rows)
    expect(filterKeywordRowsByScope(rows, "")).toEqual(rows)
    expect(filterKeywordRowsByScope(rows, SCOPE_GENERAL).map((r) => r.keyword)).toEqual([
      "switch_on",
      "switch_off",
    ])
    expect(filterKeywordRowsByScope(rows, "H6601").map((r) => r.keyword)).toEqual(["h6601_boot"])
    expect(filterKeywordRowsByScope(rows, "H9999")).toEqual([])
  })

  it("范围筛选与搜索叠加：两个条件同时生效", () => {
    const rows = buildKeywordRows(SCOPED_ENTRIES)
    const scoped = filterKeywordRowsByScope(rows, SCOPE_GENERAL)
    expect(filterKeywordRows(scoped, "关闭设备").map((r) => r.keyword)).toEqual(["switch_off"])
    expect(filterKeywordRows(scoped, "H6601")).toEqual([])
  })

  it("计数不随范围缩水：同词跨范围计 1 个关键词，同功能点跨范围计 1 个功能点", () => {
    const rows = buildKeywordRows([
      entry("switch_on", [
        { id: 0, module: "设备开关", feature: "打开设备成功", scope: "*" },
        { id: 0, module: "设备开关", feature: "打开设备成功", scope: "H6601" },
      ]),
    ])
    expect(keywordRowCounts(rows)).toEqual({ keywords: 1, features: 1 })
  })

  it("下拉选项按全量行派生：通用恒首，其余 SKU 按首次出现顺序；搜索收窄不改选项", () => {
    const rows = buildKeywordRows(SCOPED_ENTRIES)
    const expected = [
      { value: "*", label: "通用" },
      { value: "H6601", label: "H6601专用" },
      { value: "H2234", label: "H2234专用" },
    ]
    expect(scopeOptions(rows)).toEqual(expected)
    // 选项恒从全量行派生（面板接线口径）：搜索把行收窄后，选项仍按全量行取
    expect(filterKeywordRows(rows, "H6601").length).toBe(1)
    expect(scopeOptions(rows)).toEqual(expected)
  })
})
