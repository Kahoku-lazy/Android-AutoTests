import { ref } from "vue"

export function useExpandCollapse(initialOpen = []) {
  const expandedIds = ref(new Set(initialOpen))

  function toggle(id) {
    const next = new Set(expandedIds.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    expandedIds.value = next
  }

  function expand(id) {
    if (expandedIds.value.has(id)) return
    const next = new Set(expandedIds.value)
    next.add(id)
    expandedIds.value = next
  }

  function collapse(id) {
    if (!expandedIds.value.has(id)) return
    const next = new Set(expandedIds.value)
    next.delete(id)
    expandedIds.value = next
  }

  function isExpanded(id) {
    return expandedIds.value.has(id)
  }

  return { expandedIds, toggle, expand, collapse, isExpanded }
}
