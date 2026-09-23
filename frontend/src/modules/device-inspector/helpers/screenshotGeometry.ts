/**
 * 截图画布的纯几何函数——不碰 DOM、无副作用，组件只负责把 DOM 尺寸与鼠标位置
 * 换算成画布坐标后交给这里判定。
 */

/** 元素条目里可能承载坐标的字段：分层接口给 `coords`，旧响应给 `x/y/width/height` 或 `bounds` 文本 */
export interface ElementBox {
  x: number
  y: number
  w: number
  h: number
}

/** `bounds` 文本形态 `[x1,y1][x2,y2]`（唯一登记处，组件不得再写这条正则） */
const BOUNDS_RE = /\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]/

/**
 * 归一化一个元素条目的矩形，优先级：`coords{x,y,w,h}` → `x/y/width/height` → `bounds` 文本解析。
 * 三形态都拿不到合法数值时返回 null（调用方据此跳过该条目）。
 */
export function boxOf(el: unknown): ElementBox | null {
  const record = (el ?? {}) as Record<string, unknown>

  const coords = record.coords as Record<string, unknown> | undefined
  if (coords) {
    const x = Number(coords.x)
    const y = Number(coords.y)
    const w = Number(coords.w)
    const h = Number(coords.h)
    if ([x, y, w, h].every(Number.isFinite)) return { x, y, w, h }
  }

  let x = Number(record.x)
  let y = Number(record.y)
  let w = Number(record.width)
  let h = Number(record.height)
  if (![x, y, w, h].every(Number.isFinite) && typeof record.bounds === "string") {
    const matched = BOUNDS_RE.exec(record.bounds)
    if (matched) {
      x = Number(matched[1])
      y = Number(matched[2])
      w = Number(matched[3]) - x
      h = Number(matched[4]) - y
    }
  }
  if (![x, y, w, h].every(Number.isFinite)) return null
  return { x, y, w, h }
}

/**
 * 命中测试：返回包含该点且**面积最小**的元素（最具体的那个框），无命中返回 null。
 * 宽或高 ≤ 0 的条目视为不可见，不参与命中；框的四边按闭区间计算。
 */
export function pickElementAt<T>(elements: readonly T[], x: number, y: number): T | null {
  let best: T | null = null
  let bestArea = Infinity
  for (const el of elements) {
    const box = boxOf(el)
    if (!box || box.w <= 0 || box.h <= 0) continue
    if (x >= box.x && x <= box.x + box.w && y >= box.y && y <= box.y + box.h) {
      const area = box.w * box.h
      if (area > 0 && area < bestArea) {
        bestArea = area
        best = el
      }
    }
  }
  return best
}
