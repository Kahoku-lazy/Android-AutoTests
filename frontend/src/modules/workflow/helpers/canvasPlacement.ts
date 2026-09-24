/**
 * 画布落点换算 — 纯函数，不读 DOM（屏幕位置、画布原点、视口变换都由调用方传入）。
 *
 * 与 VueFlow 的 `screenToFlowCoordinate` 同源算法，但**不做网格吸附**：
 * 画布开了 16px 吸附，而落点要求节点中心精确对准鼠标，吸附会把中心推离鼠标最多 16 画布像素。
 * 行为契约见 openspec/specs/page-flow-node-placement/spec.md。
 */

export interface CanvasPoint {
  x: number
  y: number
}

/** 画布容器（VueFlow 根元素）在屏幕上的原点 */
export interface CanvasOrigin {
  left: number
  top: number
}

/** VueFlow 视口变换（平移 + 缩放） */
export interface ViewportTransform {
  x: number
  y: number
  zoom: number
}

/** 节点尺寸 */
export interface NodeSize {
  width: number
  height: number
}

/** 同一落点连续新建时的最小错位步长（画布单位） */
export const STACK_STEP: [number, number] = [24, 16]
export const STACK_MAX_STEPS = 8

/** 屏幕坐标 → 画布坐标（不吸附网格） */
export function clientToFlowPoint(
  client: CanvasPoint,
  origin: CanvasOrigin,
  viewport: ViewportTransform,
): CanvasPoint | null {
  if (!viewport.zoom) return null
  return {
    x: (client.x - origin.left - viewport.x) / viewport.zoom,
    y: (client.y - origin.top - viewport.y) / viewport.zoom,
  }
}

/** 让节点中心落在给定画布点上的节点左上角坐标 */
export function flowPointToNodePos(center: CanvasPoint, size: NodeSize): [number, number] {
  return [center.x - size.width / 2, center.y - size.height / 2]
}

/** 落点已被占用时按步长错位，最多 maxSteps 步（比较的是节点中心，与节点尺寸无关） */
export function stackingOffset(
  center: CanvasPoint,
  occupied: CanvasPoint[],
  step: [number, number] = STACK_STEP,
  maxSteps: number = STACK_MAX_STEPS,
): CanvasPoint {
  let { x, y } = center
  for (let i = 0; i < maxSteps; i++) {
    const clash = occupied.some((p) => Math.abs(p.x - x) < step[0] && Math.abs(p.y - y) < step[1])
    if (!clash) break
    x += step[0]
    y += step[1]
  }
  return { x, y }
}
