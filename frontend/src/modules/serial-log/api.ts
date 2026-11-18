/** 串口日志 API — 端口监听 / 当前日志文件 / 关键词目录（后端 apps/serial_log） */
import djangoClient from "@/shared/api-client"

// ── 无线端口（监听开关 + 当前日志文件读取）──

export interface LogPortRow {
  port: number
  /** SKU名称（被测设备型号，如 H6810） */
  sku: string
  /** 无线串口盒串口侧波特率（仅展示，不参与采集） */
  baud: number
  /** 登记来源：config=平台配置（只读基线）/ custom=页面自定义（可增删改） */
  origin: "config" | "custom" | string
  /** 完整监听地址（本机 IP:端口）；IP 未探测到时为空串 */
  address: string
  /** 监听开关：平台是否持续监听该端口 */
  enabled: boolean
  /** 运行时状态：端口此刻是否真的在监听 */
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
  /** 服务端按文件顺序给出原文行：前端 MUST NOT 再排序或拆时间 */
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

/** 新增自定义端口（仅超管）：保存即增量开启监听，返回真实监听结果 */
export async function createLogPort(payload: {
  port: number
  sku: string
  baud: number
}): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.post("/serial-log/ports/", payload)
  return data
}

/** 编辑自定义端口（仅超管）：SKU / 波特率，端口号不可改 */
export async function updateLogPort(
  port: number,
  payload: { sku?: string; baud?: number },
): Promise<{ status: boolean; data?: LogPortRow; message?: string }> {
  const { data } = await djangoClient.patch(`/serial-log/ports/${port}/`, payload)
  return data
}

/** 删除自定义端口（仅超管）：停监听、删登记，历史日志文件保留 */
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

// ── 日志关键词目录（只读，真相源 sl_log_keywords）──

/** 关键词命中的功能点（主键 + 编号 + 模块 + 名称 + 范围） */
export interface LogKeywordFeature {
  /** 条目主键（编辑 / 删除定位用） */
  row_id?: number
  id?: number
  module?: string
  feature?: string
  /** 范围："*"=通用；否则 SKU 名（如 H6601）。后端恒给出；缺省按通用兜底 */
  scope?: string
}

export interface LogKeywordEntry {
  keyword: string
  /** 一个关键词可对应多个功能点，全部带出 */
  features: LogKeywordFeature[]
}

export interface LogKeywordCatalog {
  keywords: LogKeywordEntry[]
  keyword_count: number
  feature_count: number
  /** 取值来源：数据库关键词表 / 空表或不可用 */
  origin: "db" | "none"
  /** 表内最近一次写入时间（北京时间，秒精度）；空表为空串 */
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

// ── 日志关键词维护（仅超管）──

/** 新建 / 编辑共用的表单载荷（编辑可部分提交） */
export interface LogKeywordPayload {
  keyword: string
  module: string
  feature: string
  scope: string
  feature_id?: number
}

/** 维护接口返回的单行载荷 */
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
