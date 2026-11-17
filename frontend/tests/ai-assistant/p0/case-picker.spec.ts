import { describe, expect, it } from "vitest"
import {
  countHitCases,
  filterCaseProjects,
  hitbarText,
  pickableIds,
  summarizePicked,
  toggleAll,
  type CaseProjectGroup,
} from "@/modules/ai-assistant/helpers/case-picker"

const PROJECTS: CaseProjectGroup[] = [
  {
    id: 1,
    name: "H6810 制冰机回归",
    rows: [
      { id: "H6810-01", title: "H6810 定时功能测试（UI 验证）" },
      { id: "H6810-02", title: "H6810 详情页开关与亮度功能测试（UI 验证）" },
    ],
  },
  {
    id: 2,
    name: "H705F 送风口",
    rows: [{ id: "H705F-01", title: "H705F 送风口摆风角度（UI 验证）" }],
  },
  {
    id: 3,
    name: "登录与权限",
    rows: [{ id: "AUTH-01", title: "账号被禁用后的登录提示" }],
  },
]

describe("用例选择器的过滤与分组", () => {
  it("空搜索词返回全部项目，保持原顺序", () => {
    const groups = filterCaseProjects(PROJECTS, "  ")
    expect(groups.map((group) => group.name)).toEqual([
      "H6810 制冰机回归",
      "H705F 送风口",
      "登录与权限",
    ])
    expect(countHitCases(groups)).toBe(4)
  })

  it("按编号搜索只留命中的项目与行", () => {
    const groups = filterCaseProjects(PROJECTS, "H6810-02")
    expect(groups).toHaveLength(1)
    expect(groups[0].rows.map((row) => row.id)).toEqual(["H6810-02"])
  })

  it("按名称片段搜索忽略大小写", () => {
    const groups = filterCaseProjects(PROJECTS, "h705f")
    expect(groups).toHaveLength(1)
    expect(groups[0].name).toBe("H705F 送风口")
  })

  it("没有任何命中时返回空数组", () => {
    expect(filterCaseProjects(PROJECTS, "zzz")).toEqual([])
  })

  it("可勾选编号按列表顺序铺平", () => {
    expect(pickableIds(filterCaseProjects(PROJECTS, "H6810"))).toEqual(["H6810-01", "H6810-02"])
  })
})

describe("已选的整体切换", () => {
  it("未全选时整体加入，已在选的不重复", () => {
    expect(toggleAll(["H6810-01"], ["H6810-01", "H6810-02"])).toEqual(["H6810-01", "H6810-02"])
  })

  it("已全选时整体移除", () => {
    expect(toggleAll(["H6810-01", "H6810-02", "AUTH-01"], ["H6810-01", "H6810-02"])).toEqual([
      "AUTH-01",
    ])
  })

  it("空编号不改变已选，也不改动入参", () => {
    const selected = ["H6810-01"]
    const next = toggleAll(selected, [])
    expect(next).toEqual(selected)
    expect(next).not.toBe(selected)
  })
})

describe("其他项目命中的提示文案", () => {
  it("当前项目也有命中时给两个数", () => {
    expect(hitbarText({ inScope: 2, elsewhere: 3, projectName: "H6810 制冰机回归" })).toBe(
      "当前项目命中 2 条，另有 3 条在其他项目命中",
    )
  })

  it("当前项目零命中时写明项目名", () => {
    expect(hitbarText({ inScope: 0, elsewhere: 2, projectName: "登录与权限" })).toBe(
      "「登录与权限」没有命中，另有 2 条在其他项目命中",
    )
  })

  it("没有其他项目命中时不出提示", () => {
    expect(hitbarText({ inScope: 2, elsewhere: 0, projectName: "H6810 制冰机回归" })).toBe("")
  })
})

describe("已选摘要", () => {
  it("统计条数与覆盖项目数，并列出用例名", () => {
    const summary = summarizePicked(["H6810-01", "H705F-01"], PROJECTS)
    expect(summary.count).toBe(2)
    expect(summary.projectCount).toBe(2)
    expect(summary.names).toEqual([
      "H6810 定时功能测试（UI 验证）",
      "H705F 送风口摆风角度（UI 验证）",
    ])
    expect(summary.rest).toBe(0)
  })

  it("超过 4 条时只列 4 条并折叠剩余条数", () => {
    const many: CaseProjectGroup[] = [
      {
        id: 9,
        name: "长项目",
        rows: Array.from({ length: 6 }, (_, index) => ({
          id: `CASE-${index + 1}`,
          title: `用例 ${index + 1}`,
        })),
      },
    ]
    const summary = summarizePicked(
      many[0].rows.map((row) => row.id),
      many,
    )
    expect(summary.count).toBe(6)
    expect(summary.projectCount).toBe(1)
    expect(summary.names).toEqual(["用例 1", "用例 2", "用例 3", "用例 4"])
    expect(summary.rest).toBe(2)
  })

  it("没有已选时摘要归零", () => {
    const summary = summarizePicked([], PROJECTS)
    expect(summary).toEqual({ count: 0, projectCount: 0, names: [], rest: 0 })
  })
})
