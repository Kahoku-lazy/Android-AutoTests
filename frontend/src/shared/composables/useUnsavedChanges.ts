import { onBeforeUnmount, ref, watch } from "vue"

const dirtyPages = ref(new Set<string>())
let sequence = 0

export function hasUnsavedChanges(): boolean {
  return dirtyPages.value.size > 0
}

export function useUnsavedChanges(isDirty: () => boolean): void {
  sequence += 1
  const token = `page-${sequence}`

  watch(
    isDirty,
    (value) => {
      if (value) dirtyPages.value.add(token)
      else dirtyPages.value.delete(token)
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    dirtyPages.value.delete(token)
  })
}
