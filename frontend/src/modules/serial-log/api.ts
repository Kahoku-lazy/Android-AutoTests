/** 串口日志 API — 端口监听 / 当前日志文件 / 关键词目录（后端 apps/serial_log） */
import djangoClient from "@/shared/api-client"

// ── 无线端口（监听开关 + 当前日志文件读取）──

export interface LogPortRow {
  port: number
  /** SKU名称（被测设备型号，如 H6810） */
  sku: string
  /** 无线串口盒串口侧波特率（仅展示，不参与采集） */
  baud: number
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
  data?: { ports?: LogPortRow[] }
  message?: string
}> {
  const { data } = await djangoClient.get("/serial-log/ports/")
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

// ── 日志关键词目录（只读）──

/** 关键词命中的功能点（编号 + 模块 + 名称） */
export interface LogKeywordFeature {
  id?: number
  module?: string
  feature?: string
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
  /** 取值来源：运行中的采集索引 / 配置文件 / 都取不到 */
  origin: "runtime" | "file" | "none" | string
  keyword_file: string
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
