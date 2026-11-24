import { ref, computed, watch } from "vue"

export function usePagination(source, { pageSize = 10, options = [10, 30, 50] } = {}) {
  const PAGE_SIZE_OPTIONS = options
  const size = ref(pageSize)
  const current = ref(1)

  const totalPages = computed(() => Math.max(1, Math.ceil(source.value.length / size.value)))

  const pagedItems = computed(() => {
    const start = (current.value - 1) * size.value
    return source.value.slice(start, start + size.value)
  })

  watch(totalPages, (tp) => {
    if (current.value > tp) current.value = tp
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
