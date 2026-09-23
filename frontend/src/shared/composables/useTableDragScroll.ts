/**
 * 表格左键长按后拖拽横向滑动 — 共享件（L4 数据面通用）。
 * 用法：把返回值接到承载横向滚动的外层容器上（ref + @pointerdown），
 * 该容器需 CSS `overflow-x: auto`，并关掉 el-table 自身的横向滚动，避免双滚动条。
 * 当前消费方：设备管理页（.device-table-wrapper）与设备检查器（.sap-table-body）。
 */
import { ref, onBeforeUnmount, type Ref } from 'vue'

const INTERACTIVE = 'button, a, input, textarea, select, .el-button, .el-switch, .el-checkbox'
const LONG_PRESS_MS = 180
const MOVE_ACTIVATE_PX = 6

export function useTableDragScroll(external?: Ref<HTMLElement | null>): {
  tableWrapRef: Ref<HTMLElement | null>
  onTablePointerDown: (e: PointerEvent) => void
} {
  // 默认自带 ref（模板 ref 绑定）；传入 external 时作用在调用方指定的滚动容器上
  // （例如 el-table 自身的横向滚动容器，由 EP 同步表头）
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
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    window.removeEventListener('pointercancel', onUp)
  }

  function reset(el: HTMLElement | null) {
    clearTimer()
    cleanupWindow()
    pointerId = null
    panReady = false
    el?.classList.remove('is-dragging', 'is-pan-ready')
    if (didPan) {
      const swallow = (ev: MouseEvent) => {
        ev.stopPropagation()
        ev.preventDefault()
        window.removeEventListener('click', swallow, true)
      }
      window.addEventListener('click', swallow, true)
      window.setTimeout(() => window.removeEventListener('click', swallow, true), 0)
    }
    didPan = false
  }

  function activatePan(el: HTMLElement) {
    if (panReady) return
    panReady = true
    el.classList.add('is-dragging', 'is-pan-ready')
  }

  /** 只有真正开始横移才捕获指针：
   *  pointerdown（或仅长按不动）就捕获，会把随后的 click / dblclick 重定向到
   *  本容器，使 el-table 挂在外层行上的 row-click / row-dblclick 永远收不到。 */
  function capturePointer(el: HTMLElement) {
    if (pointerId == null) return
    try {
      el.setPointerCapture(pointerId)
    } catch {
      /* ignore */
    }
  }

  function onMove(e: PointerEvent) {
    if (pointerId != null && e.pointerId !== pointerId) return
    const el = tableWrapRef.value
    if (!el) return

    const dx = e.clientX - startX
    if (!panReady && Math.abs(dx) >= MOVE_ACTIVATE_PX) {
      // 按住并滑动一小段也进入拖拽（不必干等满长按）
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
    // 仅鼠标左键 / 触控主指针
    if (e.pointerType === 'mouse' && e.button !== 0) return
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

    window.addEventListener('pointermove', onMove, { passive: false })
    window.addEventListener('pointerup', onUp)
    window.addEventListener('pointercancel', onUp)
  }

  onBeforeUnmount(() => reset(tableWrapRef.value))

  return { tableWrapRef, onTablePointerDown }
}