import { ref, onBeforeUnmount, type Ref } from "vue"

const INTERACTIVE = "button, a, input, textarea, select, .el-button, .el-switch, .el-checkbox"
const LONG_PRESS_MS = 180
const MOVE_ACTIVATE_PX = 6

export function useTableDragScroll(external?: Ref<HTMLElement | null>): {
  tableWrapRef: Ref<HTMLElement | null>
  onTablePointerDown: (e: PointerEvent) => void
} {
  const tableWrapRef = external ?? ref<HTMLElement | null>(null)

  let pointerId: number | null = null
  let startX = 0
  let startScroll = 0
  let longPressTimer: ReturnType<typeof setTimeout> | null = null
  let panReady = false
  let didPan = false

  function clearTimer() {
    if (longPressTimer != null) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }
  }

  function cleanupWindow() {
    window.removeEventListener("pointermove", onMove)
    window.removeEventListener("pointerup", onUp)
    window.removeEventListener("pointercancel", onUp)
  }

  function reset(el: HTMLElement | null) {
    clearTimer()
    cleanupWindow()
    pointerId = null
    panReady = false
    el?.classList.remove("is-dragging", "is-pan-ready")
    if (didPan) {
      const swallow = (ev: MouseEvent) => {
        ev.stopPropagation()
        ev.preventDefault()
        window.removeEventListener("click", swallow, true)
      }
      window.addEventListener("click", swallow, true)
      window.setTimeout(() => window.removeEventListener("click", swallow, true), 0)
    }
    didPan = false
  }

  function activatePan(el: HTMLElement) {
    if (panReady) return
    panReady = true
    el.classList.add("is-dragging", "is-pan-ready")
  }

  function capturePointer(el: HTMLElement) {
    if (pointerId == null) return
    try {
      el.setPointerCapture(pointerId)
    } catch {}
  }

  function onMove(e: PointerEvent) {
    if (pointerId != null && e.pointerId !== pointerId) return
    const el = tableWrapRef.value
    if (!el) return

    const dx = e.clientX - startX
    if (!panReady && Math.abs(dx) >= MOVE_ACTIVATE_PX) {
      clearTimer()
      activatePan(el)
    }
    if (!panReady) return

    capturePointer(el)
    didPan = true
    e.preventDefault()
    el.scrollLeft = startScroll - dx
  }

  function onUp(e: PointerEvent) {
    if (pointerId != null && e.pointerId !== pointerId) return
    reset(tableWrapRef.value)
  }

  function onTablePointerDown(e: PointerEvent) {
    if (e.pointerType === "mouse" && e.button !== 0) return
    const el = tableWrapRef.value
    if (!el) return
    const target = e.target as HTMLElement | null
    if (target?.closest(INTERACTIVE)) return

    reset(el)
    pointerId = e.pointerId
    startX = e.clientX
    startScroll = el.scrollLeft
    panReady = false
    didPan = false

    longPressTimer = setTimeout(() => {
      longPressTimer = null
      if (pointerId == null || !tableWrapRef.value) return
      activatePan(tableWrapRef.value)
    }, LONG_PRESS_MS)

    window.addEventListener("pointermove", onMove, { passive: false })
    window.addEventListener("pointerup", onUp)
    window.addEventListener("pointercancel", onUp)
  }

  onBeforeUnmount(() => reset(tableWrapRef.value))

  return { tableWrapRef, onTablePointerDown }
}
