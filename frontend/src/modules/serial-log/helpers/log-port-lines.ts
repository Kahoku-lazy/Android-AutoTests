/** log-port-lines — 无线端口日志窗口的纯展示函数（无状态、无 HTTP、不重排）
 *
 * 顺序的唯一真相源是服务端：按文件顺序给出原文整行。
 * 前端只按收到的顺序渲染整行，MUST NOT 再排序、拆时间或合并。
 */

import type { LogPortLine } from "../api"

/** 日志窗口可选读取行数（默认 2000，与平台配置一致） */
export const LOG_TAIL_OPTIONS = [500, 1000, 2000, 5000]

export const LOG_TAIL_DEFAULT = 2000

/** 自动刷新间隔（毫秒） */
export const LOG_AUTO_REFRESH_MS = 5000

export interface DecoratedLogLine {
  key: string
  text: string
}

/** 按收到顺序装饰日志行（整行原文，不拆时间） */
export function decorateLogLines(lines: LogPortLine[] = []): DecoratedLogLine[] {
  return (lines || []).map((line, index) => ({
    key: `${index}`,
    text: line?.text ?? "",
  }))
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

/** 行数摘要 */
export function logCountText(lineCount: number, rawLineCount: number): string {
  const count = lineCount || rawLineCount || 0
  return `${count} 条`
}

/** 文件大小 → 可读文本 */
export function formatLogSize(bytes: number): string {
  const size = Number(bytes) || 0
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

/** 关闭开关时的提示 */
export const LOG_DISABLE_WARNING = "关闭后不再监听该端口、不再写入新日志"
