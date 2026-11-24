import type { LogPortLine } from "../api"

export const LOG_TAIL_OPTIONS = [500, 1000, 2000, 5000]

export const LOG_TAIL_DEFAULT = 500

export const LOG_AUTO_REFRESH_MS = 5000

export interface DecoratedLogLine {
  key: string
  text: string
}

export function decorateLogLines(lines: LogPortLine[] = []): DecoratedLogLine[] {
  return (lines || []).map((line, index) => ({
    key: `${index}`,
    text: line?.text ?? "",
  }))
}

export function logConclusionText(conclusion: string, port: number): string {
  switch (conclusion) {
    case "no_log":
      return "当前日志文件暂无内容（设备还没推日志，或文件刚轮转过）"
    case "port_disabled":
      return `端口 ${port} 已关闭监听`
    case "port_not_configured":
      return `端口 ${port} 未配置为日志来源`
    default:
      return ""
  }
}

export function logCountText(lineCount: number, rawLineCount: number): string {
  const count = lineCount || rawLineCount || 0
  return `${count} 条`
}

export function formatLogSize(bytes: number): string {
  const size = Number(bytes) || 0
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

export const LOG_DISABLE_WARNING = "关闭后不再监听该端口、不再写入新日志"
