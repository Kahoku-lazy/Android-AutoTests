/**
 * useExpandCollapse — 通用展开/折叠 Set 模式
 *
 * 替换各模块中重复手写的：
 *   const expanded = ref(new Set())
 *   function toggle(id) { const s = new Set(expanded.value); ... }
 */
import { ref } from 'vue'

export function useExpandCollapse(initialOpen = []) {
  const expandedIds = ref(new Set(initialOpen))

  /** 切换：开→关，关→开 */
  function toggle(id) {
    const next = new Set(expandedIds.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    expandedIds.value = next
  }

  /** 强制展开 */
  function expand(id) {
    if (expandedIds.value.has(id)) return
    const next = new Set(expandedIds.value)
    next.add(id)
    expandedIds.value = next
  }

  /** 强制折叠 */
  function collapse(id) {
    if (!expandedIds.value.has(id)) return
    const next = new Set(expandedIds.value)
    next.delete(id)
    expandedIds.value = next
  }

  /** 是否已展开 */
  function isExpanded(id) {
    return expandedIds.value.has(id)
  }

  return { expandedIds, toggle, expand, collapse, isExpanded }
}
