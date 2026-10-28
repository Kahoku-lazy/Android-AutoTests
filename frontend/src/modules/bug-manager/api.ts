/** BUG 单管理 API — 唯一 HTTP 出口，统一走 /api/bugs/* */
import client, { type DjangoResponse } from "@/shared/api-client"
import type { BugListData, BugStatus, BugSyncResult, BugTicket } from "./types"

export interface BugListParams {
  category?: string
  status?: string
  keyword?: string
}

export function listBugs(
  params: BugListParams = {},
): Promise<{ data: DjangoResponse<BugListData> }> {
  return client.get("/bugs/", { params })
}

export function getBug(bugId: number): Promise<{ data: DjangoResponse<BugTicket> }> {
  return client.get(`/bugs/${bugId}/`)
}

export function updateBugStatus(
  bugId: number,
  status: BugStatus,
): Promise<{ data: DjangoResponse<BugTicket> }> {
  return client.patch(`/bugs/${bugId}/`, { status })
}

export function syncBugs(): Promise<{ data: DjangoResponse<BugSyncResult> }> {
  return client.post("/bugs/sync/")
}
