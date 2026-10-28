/**
 * [P0] BUG 单管理 — 分类标签、状态样式与任务跳转
 */
import { describe, expect, it } from "vitest"
import {
  BUG_CATEGORY_LABELS,
  BUG_CATEGORY_TABS,
  BUG_STATUS_LABELS,
  BUG_TABLE_COLUMNS,
  bugCategoryClass,
  bugStatusClass,
  bugTaskRoute,
  bugTaskStatusLabel,
  formatBugTime,
} from "@/modules/bug-manager/constants"

describe("[P0] BUG 单分类与状态", () => {
  it("分类固定为 UI 自动化与测试用例编写", () => {
    expect(BUG_CATEGORY_LABELS.ui_automation).toBe("UI 自动化")
    expect(BUG_CATEGORY_LABELS.case_authoring).toBe("测试用例编写")
    expect(BUG_CATEGORY_TABS.map((tab) => tab.key)).toEqual([
      "all",
      "ui_automation",
      "case_authoring",
    ])
  })

  it("处理状态固定为三种", () => {
    expect(BUG_STATUS_LABELS.open).toBe("待处理")
    expect(BUG_STATUS_LABELS.resolved).toBe("已解决")
    expect(BUG_STATUS_LABELS.ignored).toBe("已忽略")
    expect(bugStatusClass("resolved")).toBe("is-resolved")
    expect(bugCategoryClass("case_authoring")).toBe("is-case")
    expect(bugCategoryClass("ui_automation")).toBe("is-ui")
  })
})

describe("[P0] BUG 单任务关联", () => {
  it("任务编号跳转到任务详情", () => {
    expect(bugTaskRoute(173)).toBe("/tasks/173")
    expect(bugTaskRoute("173")).toBe("/tasks/173")
    expect(bugTaskStatusLabel("interrupted")).toBe("已中断")
  })

  it("表格保留任务编号列", () => {
    expect(BUG_TABLE_COLUMNS.some((column) => column.dataIndex === "task_id")).toBe(true)
  })

  it("空时间显示占位符", () => {
    expect(formatBugTime("")).toBe("—")
  })
})
