import { ElMessage } from "element-plus"
import { issueLogTicket, threadLogUrl } from "@/modules/ai-assistant/api/assistants"
import { fetchTaskReport } from "@/modules/task-list/api/tasks"
import { REPORT_MESSAGES } from "../constants"
import type { ReportRow } from "../types"

const BLOB_REVOKE_MS = 60_000

export function useOpenReport() {
  async function openReport(row: ReportRow) {
    try {
      if (row.source === "sop") {
        await openSopReport(row.report_run, row.report_name)
      } else {
        await openAgentReport(row.thread_id, row.report_id)
      }
    } catch (e) {
      ElMessage.error(errorMessage(e))
    }
  }

  return { openReport }
}

async function openSopReport(run: string, name: string) {
  const content = await fetchTaskReport(run, name)
  if (!content) {
    ElMessage.error(REPORT_MESSAGES.missing)
    return
  }
  const url = URL.createObjectURL(new Blob([content], { type: "text/html" }))
  window.open(url, "_blank", "noopener")
  window.setTimeout(() => URL.revokeObjectURL(url), BLOB_REVOKE_MS)
}

async function openAgentReport(threadId: string, reportId: string) {
  const ticket = await issueLogTicket(threadId, reportId)
  window.open(threadLogUrl(threadId, reportId, ticket), "_blank", "noopener")
}

function errorMessage(error: unknown): string {
  if (error && typeof error === "object") {
    const response = (error as { response?: { data?: { message?: string } } }).response
    if (response?.data?.message) return response.data.message
    const message = (error as { message?: string }).message
    if (message) return message
  }
  return REPORT_MESSAGES.openFailed
}
