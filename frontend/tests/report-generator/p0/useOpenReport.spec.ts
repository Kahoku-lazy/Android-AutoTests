/**
 * [P0] 打开报告：SOP 走正文 blob，智能体走一次性 ticket；缺失给可读提示
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ElMessage } from "element-plus"
import * as assistantApi from "@/modules/ai-assistant/api/assistants"
import * as taskApi from "@/modules/task-list/api/tasks"
import { useOpenReport } from "@/modules/report-generator/composables/useOpenReport"
import { REPORT_MESSAGES } from "@/modules/report-generator/constants"
import type { AgentReportRow, SopReportRow } from "@/modules/report-generator/types"

vi.mock("@/modules/task-list/api/tasks", () => ({
  fetchTaskReport: vi.fn(),
}))

vi.mock("@/modules/ai-assistant/api/assistants", () => ({
  issueLogTicket: vi.fn(),
  threadLogUrl: vi.fn(
    (threadId: string, reportId: string, ticket = "") =>
      `/api/ai/assistants/threads/${threadId}/logs/${reportId}/?ticket=${ticket}`,
  ),
}))

vi.mock("element-plus", () => ({
  ElMessage: { error: vi.fn(), success: vi.fn() },
}))

const sopRow: SopReportRow = {
  source: "sop",
  report_run: "20261118_102159",
  report_name: "20261118_102159_sop_bound.html",
  task_id: 173,
  task_title: "H6810 全功能测试",
  case_label: "定时",
  device: "H6810",
  status: "completed",
  started_at: "",
  finished_at: "",
  duration: "3m12s",
}

const agentRow: AgentReportRow = {
  source: "agent",
  assistant_id: "20261116_8PD",
  assistant_name: "涂鸦小助手",
  thread_id: "53c17538d163aeb4",
  report_id: "20261116_180702",
  summary: "已完成回到桌面",
  created_at: "",
}

describe("[P0] useOpenReport", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal("open", vi.fn())
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:report"),
      revokeObjectURL: vi.fn(),
    })
  })

  it("sop row fetches content and opens a blob tab", async () => {
    vi.mocked(taskApi.fetchTaskReport).mockResolvedValue("<html>报告</html>")

    const { openReport } = useOpenReport()
    await openReport(sopRow)

    expect(taskApi.fetchTaskReport).toHaveBeenCalledWith(sopRow.report_run, sopRow.report_name)
    expect(window.open).toHaveBeenCalledWith("blob:report", "_blank", "noopener")
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it("missing sop content shows readable message and does not open a tab", async () => {
    vi.mocked(taskApi.fetchTaskReport).mockResolvedValue("")

    const { openReport } = useOpenReport()
    await openReport(sopRow)

    expect(ElMessage.error).toHaveBeenCalledWith(REPORT_MESSAGES.missing)
    expect(window.open).not.toHaveBeenCalled()
  })

  it("agent row issues a ticket and opens the log url", async () => {
    vi.mocked(assistantApi.issueLogTicket).mockResolvedValue("ticket-1")

    const { openReport } = useOpenReport()
    await openReport(agentRow)

    expect(assistantApi.issueLogTicket).toHaveBeenCalledWith(agentRow.thread_id, agentRow.report_id)
    expect(window.open).toHaveBeenCalledWith(
      `/api/ai/assistants/threads/${agentRow.thread_id}/logs/${agentRow.report_id}/?ticket=ticket-1`,
      "_blank",
      "noopener",
    )
  })

  it("ticket failure surfaces a readable message", async () => {
    vi.mocked(assistantApi.issueLogTicket).mockRejectedValue(new Error("还在写"))

    const { openReport } = useOpenReport()
    await openReport(agentRow)

    expect(ElMessage.error).toHaveBeenCalledWith("还在写")
    expect(window.open).not.toHaveBeenCalled()
  })
})
