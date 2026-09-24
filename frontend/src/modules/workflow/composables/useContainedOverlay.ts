/**
 * 光标锚定浮层的视口收敛 — 组件只把 `el` 挂到浮层根元素、读 `position` 渲染。
 *
 * 先按兜底尺寸算出屏内位置（保证第一帧就在屏内），渲染后按实测尺寸再精修一次。
 */
import { nextTick, ref, type Ref } from "vue"
import {
  containOverlayPosition,
  currentViewport,
  measuredOrFallback,
  type OverlayPoint,
  type OverlaySize,
} from "@/modules/workflow/helpers/overlayPosition"

export interface ContainedOverlay {
  /** 挂到浮层根元素，用于实测尺寸 */
  el: Ref<HTMLElement | null>
  /** 已收敛的 left / top */
  position: Ref<OverlayPoint>
  /** 按锚点落位：同步一次（用兜底尺寸），渲染后按实测尺寸再收敛一次 */
  place: (anchor: OverlayPoint) => Promise<void>
}

export function useContainedOverlay(fallback: OverlaySize): ContainedOverlay {
  const el = ref<HTMLElement | null>(null)
  const position = ref<OverlayPoint>({ x: 0, y: 0 })

  function apply(anchor: OverlayPoint): void {
    const rect = el.value?.getBoundingClientRect()
    const size = measuredOrFallback(
      { width: rect?.width ?? 0, height: rect?.height ?? 0 },
      fallback,
    )
    position.value = containOverlayPosition(anchor, size, currentViewport())
  }

  async function place(anchor: OverlayPoint): Promise<void> {
    apply(anchor)
    await nextTick()
    apply(anchor)
  }

  return { el, position, place }
}
