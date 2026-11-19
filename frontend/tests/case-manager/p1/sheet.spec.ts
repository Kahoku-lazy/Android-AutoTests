/**
 * [P1] 用例表视图与草稿纯函数
 */
import { describe, expect, it } from "vitest"
import { isReactive, reactive } from "vue"
import {
  applySheetView,
  buildDisplayRows,
  businessLabel,
  cloneRow,
  editablePayload,
  groupRows,
  hasAnchor,
  hasLog,
  isGroupHeader,
  priorityTone,
  sortRows,
  stepSummary,
  validateDraft,
} from "@/modules/case-manager/helpers/sheet"
import { DEFAULT_SHEET_VIEW } from "@/modules/case-manager/types"
import type { CaseRow, Priority, SheetView } from "@/modules/case-manager/types"

function makeRow(id: string, patch: Partial<CaseRow> = {}): CaseRow {
  return {
    id,
    project_id: 1,
    title: `用例 ${id}`,
    priority: "P1" as Priority,
    system: "ANDROID",
    business_type: "lighting",
    module: "定时",
    precondition: "",
    steps: [{ action: "打开详情页", assertion: "标题可见" }],
    step_count: 1,
    sort_order: 1,
    updated_at: "2026-11-17T19:12:34Z",
    ...patch,
  }
}

function makeView(patch: Partial<SheetView> = {}): SheetView {
  return { ...DEFAULT_SHEET_VIEW, ...patch }
}

describe("[P1] 视图计算", () => {
  it("隐式空视图保留全部行", () => {
    const rows = [makeRow("a"), makeRow("b")]
    expect(applySheetView(rows, makeView())).toHaveLength(2)
  })

  it("按优先级筛选只留命中行", () => {
    const rows = [makeRow("a", { priority: "P0" }), makeRow("b", { priority: "P1" })]
    const out = applySheetView(rows, makeView({ filters: { priority: "P0" } }))
    expect(out.flatMap((row) => (isGroupHeader(row) ? [] : [row.id]))).toEqual(["a"])
  })

  it("分组时插入组头行，且组头条数为组内行数", () => {
    const rows = [
      makeRow("a", { priority: "P0" }),
      makeRow("b", { priority: "P1" }),
      makeRow("c", { priority: "P1" }),
    ]
    const out = applySheetView(rows, makeView({ group_by: "priority" }))
    const headers = out.filter(isGroupHeader)
    expect(headers.map((row) => row.__group)).toEqual(["P0", "P1"])
    expect(headers[1].__count).toBe(2)
    expect(out).toHaveLength(5)
  })

  it("不分组时不插组头", () => {
    const groups = groupRows([makeRow("a")], "")
    expect(buildDisplayRows(groups)).toHaveLength(1)
  })

  it("sort_order 按数值比较而不是按字符串", () => {
    const rows = [makeRow("ten", { sort_order: 10 }), makeRow("two", { sort_order: 2 })]
    expect(sortRows(rows, { field: "sort_order", direction: "asc" }).map((row) => row.id)).toEqual([
      "two",
      "ten",
    ])
  })
})

describe("[P1] 草稿读写", () => {
  it("cloneRow 深拷贝步骤与执行提示", () => {
    const row = makeRow("a", {
      steps: [
        {
          action: "打开",
          assertion: "可见",
          anchor: { page: "详情" },
          log: { sku: "H705F", port: 1, keywords: ["ok"] },
        },
      ],
    })
    const draft = cloneRow(row)
    draft.steps[0].action = "改了"
    draft.steps[0].log?.keywords?.push("extra")

    expect(row.steps[0].action).toBe("打开")
    expect(row.steps[0].log?.keywords).toEqual(["ok"])
  })

  // 回归：自动化项目的空执行提示是 {} 而不是缺键，按字段重建会抛 TypeError，抽屉打不开
  it("cloneRow 遇到空执行提示 {} 不抛错且原样保留", () => {
    const row = makeRow("a", {
      steps: [{ action: "打开", assertion: "可见", anchor: {}, log: {} }],
    })
    expect(() => cloneRow(row)).not.toThrow()
    const draft = cloneRow(row)
    expect(draft.steps[0].anchor).toEqual({})
    expect(draft.steps[0].log).toEqual({})
  })

  // 回归：表格行是 reactive Proxy，structuredClone 对 Proxy 会抛 DataCloneError
  it("cloneRow 能吃下 reactive 行并返回普通对象", () => {
    const row = reactive(
      makeRow("a", { steps: [{ action: "打开", assertion: "可见", anchor: {}, log: {} }] }),
    )
    expect(() => cloneRow(row as CaseRow)).not.toThrow()
    const draft = cloneRow(row as CaseRow)
    expect(isReactive(draft)).toBe(false)
    expect(draft.steps[0].action).toBe("打开")
  })

  it("hasAnchor / hasLog 按内容判空，{} 视为没有", () => {
    expect(hasAnchor({ action: "a", assertion: "b", anchor: {} })).toBe(false)
    expect(hasLog({ action: "a", assertion: "b", log: {} })).toBe(false)
    expect(hasAnchor({ action: "a", assertion: "b", anchor: { page: "详情" } })).toBe(true)
    expect(hasLog({ action: "a", assertion: "b", log: { sku: "S" } })).toBe(true)
  })

  it("editablePayload 只带可写字段并去空白", () => {
    const payload = editablePayload(makeRow("a", { title: "  定时用例  ", module: " 定时 " }))
    expect(payload.title).toBe("定时用例")
    expect(payload.module).toBe(" 定时 ")
    expect(payload).not.toHaveProperty("step_count")
    expect(payload).not.toHaveProperty("updated_at")
  })

  it("editablePayload 不发空执行提示，保留非空提示", () => {
    const payload = editablePayload(
      makeRow("a", {
        steps: [
          { action: "空提示", assertion: "b", anchor: {}, log: {} },
          {
            action: "有提示",
            assertion: "b",
            anchor: { page: "详情" },
            log: { sku: "H705F", port: 1, keywords: ["ok"] },
          },
        ],
      }),
    )
    const steps = payload.steps || []
    expect(steps[0]).not.toHaveProperty("anchor")
    expect(steps[0]).not.toHaveProperty("log")
    expect(steps[1].anchor).toEqual({ page: "详情" })
    expect(steps[1].log?.keywords).toEqual(["ok"])
  })

  it("标题为空被拒", () => {
    expect(validateDraft(makeRow("a", { title: "   " }))?.message).toContain("标题")
  })

  it("零步骤被拒", () => {
    const row = makeRow("a", { steps: [], step_count: 0 })
    expect(validateDraft(row)?.message).toContain("1 条步骤")
  })

  it("第 2 步断言为空时指出步骤序号", () => {
    const row = makeRow("a", {
      steps: [
        { action: "A", assertion: "断言 A" },
        { action: "B", assertion: "  " },
      ],
    })
    const issue = validateDraft(row)
    expect(issue?.step).toBe(2)
    expect(issue?.message).toContain("第 2 步")
  })

  it("超过 2000 字被拒", () => {
    const row = makeRow("a", {
      steps: [{ action: "A".repeat(2001), assertion: "断言" }],
    })
    expect(validateDraft(row)?.message).toContain("2000")
  })
})

describe("[P1] 展示文案", () => {
  it("优先级映射色调", () => {
    expect(priorityTone("P0")).toBe("p0")
    expect(priorityTone("P2")).toBe("p2")
  })

  it("业务枚举翻中文，未知值原样返回", () => {
    expect(businessLabel("lighting")).toBe("照明")
    expect(businessLabel("unknown")).toBe("unknown")
  })

  it("步骤摘要", () => {
    expect(stepSummary(5)).toBe("5 步")
    expect(stepSummary(0)).toBe("0 步")
  })
})
