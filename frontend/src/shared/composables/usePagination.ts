import { ref, computed } from 'vue'

/**
 * Standard pagination for a filtered reactive list.
 *
 * @param {import('vue').Ref<Array>} source — reactive data source to paginate
 * @param {{ pageSize?: number, options?: number[] }} [opts]
 * @param {number} [opts.pageSize=10] — items per page
 * @param {number[]} [opts.options=[10,30,50]] — available page size choices
 * @returns {{
 *   PAGE_SIZE_OPTIONS: number[],
 *   pageSize: import('vue').Ref<number>,
 *   currentPage: import('vue').Ref<number>,
 *   totalPages: import('vue').ComputedRef<number>,
 *   pagedItems: import('vue').ComputedRef<Array>,
 *   setPageSize: (size: number) => void,
 *   goPage: (page: number) => void,
 * }}
 *
 * @example
 *   const { pageSize, currentPage, totalPages, pagedItems, setPageSize, goPage }
 *     = usePagination(filteredSource, { pageSize: 10, options: [10, 30, 50] })
 *
 * @example
 *   // In template:
 *   <button v-for="n in PAGE_SIZE_OPTIONS" ...>{{ n }}</button>
 *   第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredItems.length }} 条
 *   <AnimalButton :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</AnimalButton>
 *   <AnimalButton :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</AnimalButton>
 */
export function usePagination(source, { pageSize = 10, options = [10, 30, 50] } = {}) {
  const PAGE_SIZE_OPTIONS = options
  const size = ref(pageSize)
  const current = ref(1)

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(source.value.length / size.value)),
  )

  const pagedItems = computed(() => {
    const start = (current.value - 1) * size.value
    return source.value.slice(start, start + size.value)
  })

  function setPageSize(s) {
    size.value = s
    current.value = 1
  }

  function goPage(page) {
    const p = Math.max(1, Math.min(page, totalPages.value))
    if (p !== current.value) current.value = p
  }

  return {
    PAGE_SIZE_OPTIONS,
    pageSize: size,
    currentPage: current,
    totalPages,
    pagedItems,
    setPageSize,
    goPage,
  }
}
