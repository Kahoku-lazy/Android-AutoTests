/** model-debug-trace — 调试页工具调用轨迹的展示派生（纯函数，无状态无副作用） */
import type { ModelDebugToolCall } from "../api/toolbox"

/** 工具名 → 只读标记；轨迹里出现未知工具时不贴徽标（不猜） */
export function readOnlyByName(
  tools: { name: string; read_only: boolean }[],
): Map<string, boolean> {
  const map = new Map<string, boolean>()
  for (const tool of tools) map.set(tool.name, tool.read_only)
  return map
}

/** 轨迹里某工具名的只读标记；未登记时返回 undefined（调用方据此不贴徽标） */
export function toolReadOnly(map: Map<string, boolean>, name: string): boolean | undefined {
  return map.get(name)
}

/** 轨迹单条的入参 / 返回文本；超过 limit 时截断（action_time / screenshot_path 等尾部字段必须看得到） */
export function traceDetail(call: ModelDebugToolCall, limit: number): string {
  const raw = call.type === "call" ? JSON.stringify(call.input ?? {}) : call.output || ""
  return raw.length > limit ? raw.slice(0, limit) + "…" : raw
}
