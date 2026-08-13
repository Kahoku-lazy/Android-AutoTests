import { ref, computed } from 'vue'

/**
 * Standard Tabs-based filter for a reactive list.
 *
 * Combines a reactive `activeFilter` ref with a computed `filteredItems` list
 * and `filterTabs` array compatible with the `<AppTabs>` shared component.
 *
 * @param {import('vue').Ref<Array>} source — reactive source list
 * @param {Record<string, {label: string, [key: string]: any}>} tabDefs — map of tab key → definition
 * @param {(item: any, key: string) => boolean} matchFn — filter predicate; `key === 'all'` always passed through
 * @returns {{
 *   activeFilter: import('vue').Ref<string>,
 *   filterTabs: import('vue').ComputedRef<Array<{key: string, label: string}>>,
 *   filteredItems: import('vue').ComputedRef<Array>,
 * }}
 *
 * @example
 *   const { activeFilter, filterTabs, filteredItems } = useFilterTabs(
 *     sourceList,
 *     { all: { label: '全部' }, running: { label: '运行中' } },
 *     (item, key) => key === 'all' || item.status === key,
 *   )
 *
 * @example
 *   // In template:
 *   <Tabs :items="filterTabs" v-model="activeFilter" :leaf-animation="true" :shadow="true">
 *     <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
 *       ...
 *     </template>
 *   </Tabs>
 */
export function useFilterTabs(source, tabDefs: Record<string, any>, matchFn) {
  const activeFilter = ref('all')

  const filterTabs = Object.entries(tabDefs).map(([key, def]) => ({
    key,
    label: def.label,
    ...def,
  }))

  const filteredItems = computed(() => {
    if (activeFilter.value === 'all') return source.value
    return source.value.filter((item) => matchFn(item, activeFilter.value))
  })

  return { activeFilter, filterTabs, filteredItems }
}
