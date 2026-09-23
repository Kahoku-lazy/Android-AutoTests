/** 模型调试页：把角色工具按后端给出的 category 分组（保持后端下发顺序） */
import type { ModelDebugTool } from "../api/toolbox"

export interface ModelDebugToolGroup {
  category: string
  /** 该分类下已启用的工具数 */
  enabled: number
  /** 该分类下的工具总数 */
  total: number
  items: ModelDebugTool[]
}

export function groupToolsByCategory(tools: ModelDebugTool[]): ModelDebugToolGroup[] {
  const groups = new Map<string, ModelDebugToolGroup>()
  for (const tool of tools) {
    let group = groups.get(tool.category)
    if (!group) {
      group = { category: tool.category, enabled: 0, total: 0, items: [] }
      groups.set(tool.category, group)
    }
    group.total += 1
    if (tool.enabled) group.enabled += 1
    group.items.push(tool)
  }
  return [...groups.values()]
}
