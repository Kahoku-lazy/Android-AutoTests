import djangoClient from "@/shared/api-client"

export interface LogPortRow {
  port: number

  sku: string

  baud: number

  origin: "config" | "custom" | string

  address: string

  enabled: boolean

  listening: boolean
  log_file: string
  size_bytes: number
  note: string
}

export interface LogPortLine {
  text: string
}

export interface LogPortLinesPayload {
  port: number
  sku: string
  log_file: string
  tail: number
  line_count: number
  raw_line_count: number

  lines: LogPortLine[]
  conclusion: "ok" | "no_log" | "port_not_configured" | "port_disabled" | string
  note: string
}

export async function fetchLogPorts(): Promise<{
  status: boolean
  data?: { ports?: LogPortRow[]; listen_ip?: string }
  message?: string
}> {
  const { data } = await djangoClient.get("/serial-log/ports/")
  return data
}

export async function createLogPort(payload: {
  port: number
  sku: string
  baud: number
}): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.post("/serial-log/ports/", payload)
  return data
}

export async function updateLogPort(
  port: number,
  payload: { sku?: string; baud?: number },
): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.patch(`/serial-log/ports/${port}/`, payload)
  return data
}

export async function deleteLogPort(port: number): Promise<{
  status: boolean
  data?: { port: number; deleted: boolean; note: string }
  message?: string
}> {
  const { data } = await djangoClient.delete(`/serial-log/ports/${port}/`)
  return data
}

export async function toggleLogPort(
  port: number,
  enabled: boolean,
): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.post("/serial-log/ports/toggle/", { port, enabled })
  return data
}

export async function fetchLogPortLines(
  port: number,
  tail: number,
): Promise<{ status: boolean; data?: LogPortLinesPayload; message?: string }> {
  const { data } = await djangoClient.get(`/serial-log/ports/${port}/lines/`, { params: { tail } })
  return data
}

export interface LogKeywordFeature {
  row_id?: number
  id?: number
  module?: string
  feature?: string

  scope?: string
}

export interface LogKeywordEntry {
  keyword: string

  features: LogKeywordFeature[]
}

export interface LogKeywordCatalog {
  keywords: LogKeywordEntry[]
  keyword_count: number
  feature_count: number

  origin: "db" | "none"

  updated_at: string
  note: string
}

export async function fetchLogKeywords(): Promise<{
  status: boolean
  data?: LogKeywordCatalog
  message?: string
}> {
  const { data } = await djangoClient.get("/serial-log/keywords/")
  return data
}

export interface LogKeywordPayload {
  keyword: string
  module: string
  feature: string
  scope: string
  feature_id?: number
}

export interface LogKeywordRowPayload {
  row_id: number
  keyword: string
  feature_id: number
  module: string
  feature: string
  scope: string
  sort_order: number
}

export async function createLogKeyword(payload: LogKeywordPayload): Promise<{
  status: boolean
  data?: { row: LogKeywordRowPayload }
  message?: string
}> {
  const { data } = await djangoClient.post("/serial-log/keywords/", payload)
  return data
}

export async function updateLogKeyword(
  rowId: number,
  payload: Partial<LogKeywordPayload> & { sort_order?: number },
): Promise<{ status: boolean; data?: { row: LogKeywordRowPayload }; message?: string }> {
  const { data } = await djangoClient.patch(`/serial-log/keywords/${rowId}/`, payload)
  return data
}

export async function deleteLogKeyword(rowId: number): Promise<{
  status: boolean
  data?: { deleted: boolean; note: string }
  message?: string
}> {
  const { data } = await djangoClient.delete(`/serial-log/keywords/${rowId}/`)
  return data
}
