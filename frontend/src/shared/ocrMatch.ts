/**
 * OCR 文本 ↔ dump 元素几何匹配（方案 A：中心点包含 + 最小面积）。
 *
 * 背景：dump 元素 bounds 是「控件外框」，OCR 框是「文字字形框」，二者同一像素
 * 坐标系但尺寸/位置天然不同，精确坐标全等几乎不可能命中；且 Android 层级嵌套，
 * 同一 OCR 中心点会同时落在多层容器 bounds 内。故取「中心点包含 + 面积最小」，
 * 定位到最具体的叶子元素。
 *
 * 一对一：一条 OCR 至多匹配一个元素；一个元素至多匹配一条 OCR（先到先得，
 * 某元素再次被命中时，后续 OCR 视为未匹配）。
 */

export interface OcrMatchPoint {
  x: number
  y: number
  width: number
  height: number
}

export interface OcrMatchResult<TText> {
  /** 元素数组下标 → 匹配到的 OCR 文本（保留原对象引用） */
  byElement: Map<number, TText>
  /** 已匹配的 OCR 下标集合（供「未匹配 OCR 独立成行」） */
  matchedOcrIndexes: Set<number>
}

export function matchOcrToElements<TElement extends OcrMatchPoint, TText extends OcrMatchPoint>(
  elements: TElement[],
  ocrTexts: TText[],
): OcrMatchResult<TText> {
  const byElement = new Map<number, TText>()
  const matchedOcrIndexes = new Set<number>()
  const usedElements = new Set<number>()

  // 预计算元素 box 与面积，避免热路径重复运算
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
