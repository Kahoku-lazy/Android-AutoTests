import type { PlatformToolParamSchema } from "../api/toolbox"

/**
 * 参数标签 = 中文名（english_name）。
 *
 * 英文参数名必须保留可见：排查时要与接口入参对得上。
 * 中文名缺失（服务端未登记）或与英文名相同时只显示英文名，避免「keyword（keyword）」这种重复。
 */
export function paramLabel(param: PlatformToolParamSchema): string {
  const label = String(param.label || "").trim()
  if (!label || label === param.name) return param.name
  return `${label}（${param.name}）`
}
