/**
 * 媒体相对路径 → 可展示 URL 的唯一登记处（后端媒体约定：相对路径拼 `/media/`）。
 * 无路径时不产 URL —— 空串既避免请求站点根，也让调用方可用 `v-if` 直接判空。
 */
export function mediaUrl(path?: string | null): string {
  return path ? `/media/${path}` : ''
}
