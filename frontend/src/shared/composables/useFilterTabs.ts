import { ref, computed } from "vue"

export function useFilterTabs(source, tabDefs: Record<string, any>, matchFn) {
  const activeFilter = ref("all")

  const filterTabs = Object.entries(tabDefs).map(([key, def]) => ({
    key,
    label: def.label,
    ...def,
  }))

  const filteredItems = computed(() => {
    if (activeFilter.value === "all") return source.value
    return source.value.filter((item) => matchFn(item, activeFilter.value))
  })

  return { activeFilter, filterTabs, filteredItems }
}
