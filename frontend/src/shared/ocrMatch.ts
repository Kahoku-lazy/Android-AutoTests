export interface OcrMatchPoint {
  x: number
  y: number
  width: number
  height: number
}

export interface OcrMatchResult<TText> {
  byElement: Map<number, TText>

  matchedOcrIndexes: Set<number>
}

export function matchOcrToElements<TElement extends OcrMatchPoint, TText extends OcrMatchPoint>(
  elements: TElement[],
  ocrTexts: TText[],
): OcrMatchResult<TText> {
  const byElement = new Map<number, TText>()
  const matchedOcrIndexes = new Set<number>()
  const usedElements = new Set<number>()

  const boxes = elements.map((e) => {
    const w = e.width || 0
    const h = e.height || 0
    return { x: e.x || 0, y: e.y || 0, w, h, area: w * h }
  })

  ocrTexts.forEach((t, oi) => {
    const cx = (t.x || 0) + (t.width || 0) / 2
    const cy = (t.y || 0) + (t.height || 0) / 2
    let best = -1
    let bestArea = Infinity
    boxes.forEach((b, ei) => {
      if (b.area <= 0) return
      if (cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h) {
        if (b.area < bestArea) {
          bestArea = b.area
          best = ei
        }
      }
    })
    if (best >= 0 && !usedElements.has(best)) {
      usedElements.add(best)
      matchedOcrIndexes.add(oi)
      byElement.set(best, t)
    }
  })

  return { byElement, matchedOcrIndexes }
}
