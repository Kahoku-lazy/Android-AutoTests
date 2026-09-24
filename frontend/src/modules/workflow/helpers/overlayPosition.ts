/**
 * 画布内光标锚定浮层的视口收敛 — 纯函数，不读 DOM。
 *
 * 视口尺寸由调用方注入，尺寸实测值也由调用方传入，因此本文件可在无浏览器环境单测。
 * 行为契约见 openspec/specs/page-flow-overlay-containment/spec.md。
 */

export interface OverlayPoint {
  x: number
  y: number
}

export interface OverlaySize {
  width: number
  height: number
}

/** 浮层与视口边缘的最小间距 */
export const OVERLAY_MARGIN = 8

/** 兜底尺寸：与各浮层 CSS 的 width / max-height 声明保持一致（实测尺寸不可用时使用） */
export const NODE_MENU_SIZE: OverlaySize = { width: 288, height: 420 }
export const EDGE_MENU_SIZE: OverlaySize = { width: 248, height: 200 }
export const ELEMENT_PICKER_SIZE: OverlaySize = { width: 340, height: 420 }

/** 当前视口尺寸；非浏览器环境返回 0，由调用方的兜底尺寸接手 */
export function currentViewport(): OverlaySize {
  if (typeof window === "undefined") return { width: 0, height: 0 }
  return { width: window.innerWidth, height: window.innerHeight }
}

/** 实测尺寸有效（> 0）则用实测值，否则回落常量 */
export function measuredOrFallback(measured: OverlaySize, fallback: OverlaySize): OverlaySize {
  return {
    width: measured.width > 0 ? measured.width : fallback.width,
    height: measured.height > 0 ? measured.height : fallback.height,
  }
}

/**
 * 把光标锚点收敛到视口内：右/下越界时向左/上平移，始终保留 margin 间距。
 * 浮层比视口还大时贴到 margin（高度再由 CSS 的 max-height 收敛，内部列表滚动）。
 */
export function containOverlayPosition(
  anchor: OverlayPoint,
  size: OverlaySize,
  viewport: OverlaySize,
  margin: number = OVERLAY_MARGIN,
): OverlayPoint {
  const maxX = viewport.width - size.width - margin
  const maxY = viewport.height - size.height - margin
  return {
    x: Math.max(margin, Math.min(anchor.x, maxX)),
    y: Math.max(margin, Math.min(anchor.y, maxY)),
  }
}
