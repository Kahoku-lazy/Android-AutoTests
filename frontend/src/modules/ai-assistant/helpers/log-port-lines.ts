/** log-port-lines — 无线端口日志窗口的纯展示函数（无状态、无 HTTP、不重排）
 *
 * 排序与合并的唯一真相源是**服务端**：同毫秒合并为一条、最新时间在最上面。
 * 前端只做「按收到顺序渲染」与文案映射，MUST NOT 再排序或再合并（否则两条口径会漂移）。
 */

import type { LogPortLine } from "../api/toolbox"

/** 日志窗口可选读取行数（默认 2000，与平台配置一致） */
export const LOG_TAIL_OPTIONS = [500, 1000, 2000, 5000]

export const LOG_TAIL_DEFAULT = 2000

/** 自动刷新间隔（毫秒） */
export const LOG_AUTO_REFRESH_MS = 5000

export interface DecoratedLogLine {
  /** 渲染 key：时间戳 + 序号（同一时刻可能有多条不同来源） */
  key: string
  timestamp: string
  /** 时刻部分 `HH:MM:SS.mmm`（列表里更省横向空间） */
  clock: string
  source: string
  text: string
  /** 合并条（同一毫秒多行）→ 展示时保留换行 */
  merged: boolean
}

/** 时刻部分：`2026-09-28 15:47:41.466` → `15:47:41.466` */
export function clockOf(timestamp: string): string {
  const text = (timestamp || "").trim()
  const space = text.indexOf(" ")
  return space >= 0 ? text.slice(space + 1) : text
}

/** 按收到顺序装饰日志行（保持服务端顺序与合并条内部换行） */
export function decorateLogLines(lines: LogPortLine[] = []): DecoratedLogLine[] {
  return (lines || []).map((line, index) => {
    const text = line?.text ?? ""
    return {
      key: `${line?.timestamp ?? ""}#${index}`,
      timestamp: line?.timestamp ?? "",
      clock: clockOf(line?.timestamp ?? ""),
      source: line?.source ?? "",
      text,
      merged: text.includes("\n"),
    }
  })
}

/** 结论 → 中文提示（`ok` 不提示） */
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

/** 行数摘要：合并条数 + 合并前原始行数 */
export function logCountText(lineCount: number, rawLineCount: number): string {
  if (!lineCount) return "0 条"
  if (rawLineCount > lineCount) return `${lineCount} 条（原始 ${rawLineCount} 行，同毫秒已合并）`
  return `${lineCount} 条`
}

/** 文件大小 → 可读文本 */
export function formatLogSize(bytes: number): string {
  const size = Number(bytes) || 0
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

/** 关闭开关时的降级提示（页面必须明确告知，避免「验收变弱」被误读成缺陷） */
export const LOG_DISABLE_WARNING = "关闭后 AI 设备任务验收将没有该端口的日志证据（只剩页面截图）"
