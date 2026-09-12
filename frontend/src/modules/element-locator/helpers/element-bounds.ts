/** 解析 Android bounds / 数值坐标 → 矩形 */

const BOUNDS_PATTERN = /\[(\d+),(\d+)\]\[(\d+),(\d+)\]/

export interface ElementRect {
  x: number
  y: number
  width: number
  height: number
}

export function resolveElementRect(input: {
  x?: number
  y?: number
  width?: number
  height?: number
  bounds?: string
}): ElementRect | null {
  const width = Number(input.width) || 0
  const height = Number(input.height) || 0
  if (width > 0 && height > 0) {
    return {
      x: Number(input.x) || 0,
      y: Number(input.y) || 0,
      width,
      height,
    }
  }
  const raw = String(input.bounds || '').trim()
  if (!raw) return null
  const matched = raw.match(BOUNDS_PATTERN)
  if (!matched) return null
  const x1 = Number(matched[1])
  const y1 = Number(matched[2])
  const x2 = Number(matched[3])
  const y2 = Number(matched[4])
  const w = x2 - x1
  const h = y2 - y1
  if (w <= 0 || h <= 0) return null
  return { x: x1, y: y1, width: w, height: h }
}

export function mediaPathToUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('/media/')) {
    return path
  }
  return `/media/${path.replace(/^\/+/, '')}`
}
