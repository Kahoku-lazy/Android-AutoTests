import { ref, watch } from 'vue'

/**
 * Reactive localStorage binding with JSON serialization.
 *
 * Automatically persists changes via `watch` with `{ deep: true }`.
 * Use for objects, arrays, and complex values that need JSON round-trip.
 *
 * @template T
 * @param {string} key — localStorage key (convention: `'{module}:{key}'`, e.g. `'case-manager:viewMode'`)
 * @param {T} [defaultValue=null] — fallback when key is absent or parse fails
 * @returns {import('vue').Ref<T>} — reactive ref that auto-persists to localStorage on change
 *
 * @example
 *   const viewMode = useStorage('case-manager:viewMode', 'card')
 *   viewMode.value = 'table'  // auto-persisted
 */
export function useStorage(key, defaultValue = null) {
  function read() {
    try {
      const raw = localStorage.getItem(key)
      return raw !== null ? JSON.parse(raw) : defaultValue
    } catch {
      return defaultValue
    }
  }

  const val = ref(read())

  watch(
    val,
    (v) => {
      try {
        localStorage.setItem(key, JSON.stringify(v))
      } catch { /* quota exceeded — silently ignore */ }
    },
    { deep: true },
  )

  return val
}

/**
 * Raw string-only storage binding (no JSON parse/stringify).
 *
 * For simple values like tokens, user ids. No deep watch — only triggers on ref assignment.
 *
 * @param {string} key — localStorage key
 * @param {string} [defaultValue=''] — fallback when key is absent
 * @returns {import('vue').Ref<string>} — reactive ref that auto-persists to localStorage
 */
export function useRawStorage(key, defaultValue = '') {
  function read() {
    try { return localStorage.getItem(key) ?? defaultValue }
    catch { return defaultValue }
  }

  const val = ref(read())

  watch(val, (v) => {
    try { localStorage.setItem(key, v ?? '') }
    catch { /* ignore */ }
  })

  return val
}
