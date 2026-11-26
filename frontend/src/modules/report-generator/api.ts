import client, { type DjangoResponse } from "@/shared/api-client"
import type { ReportListData } from "./types"

export interface ReportListParams {
  source?: string
  keyword?: string
  start_date?: string
  end_date?: string
}

export function listReports(
  params: ReportListParams = {},
): Promise<{ data: DjangoResponse<ReportListData> }> {
  return client.get("/reports/", { params })
}
