import { describe, expect, it } from "vitest"
import {
  formatReportTime,
  identitySub,
  identityTitle,
  outcomeText,
  relationLabel,
  reportMoment,
  reportRowKey,
} from "@/modules/report-generator/helpers/report-row"
import type { AgentReportRow, SopReportRow } from "@/modules/report-generator/types"

const sopRow: SopReportRow = {
  source: "sop",
  report_run: "20261118_102159",
  report_name: "20261118_102159_sop_bound.html",
  task_id: 173,
  task_title: "H6810 全功能测试",
  case_label: "定时 · 共 2 条",
  device: "H6810",
  status: "completed",
  started_at: "2026-11-18T10:21:59+08:00",
  finished_at: "2026-11-18T10:25:11+08:00",
  duration: "3m12s",
}

const agentRow: AgentReportRow = {
  source: "agent",
  assistant_id: "20261116_8PD",
  assistant_name: "涂鸦小助手",
  thread_id: "53c17538d163aeb4",
  report_id: "20261116_180702",
  summary: "已完成回到桌面",
  created_at: "2026-11-16T18:07:02+08:00",
}

describe("[P0] report row identity", () => {
  it("sop row shows case label and task id", () => {
    expect(identityTitle(sopRow)).toBe("定时 · 共 2 条")
    expect(identitySub(sopRow)).toBe("H6810 全功能测试")
    expect(relationLabel(sopRow)).toBe("#173")
    expect(outcomeText(sopRow)).toBe("H6810 · 3m12s")
    expect(reportMoment(sopRow)).toBe(sopRow.finished_at)
  })

  it("sop row without case identity falls back to task title", () => {
    expect(identityTitle({ ...sopRow, case_label: "" })).toBe("H6810 全功能测试")
  })

  it("agent row shows assistant name and id", () => {
    expect(identityTitle(agentRow)).toBe("涂鸦小助手")
    expect(identitySub(agentRow)).toBe("20261116_8PD")
    expect(relationLabel(agentRow)).toBe("53c17538d163aeb4")
    expect(outcomeText(agentRow)).toBe("已完成回到桌面")
    expect(reportMoment(agentRow)).toBe(agentRow.created_at)
  })

  it("deleted assistant card falls back to id", () => {
    expect(identityTitle({ ...agentRow, assistant_name: "" })).toBe("20261116_8PD")
  })

  it("row keys never collide across sources", () => {
    expect(reportRowKey(sopRow)).not.toBe(reportRowKey(agentRow))
    expect(reportRowKey(sopRow)).toContain(sopRow.report_name)
    expect(reportRowKey(agentRow)).toContain(agentRow.report_id)
  })

  it("empty time shows placeholder", () => {
    expect(formatReportTime("")).toBe("—")
  })
})
