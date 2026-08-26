/**
 * [P0] 必测 — OCR ↔ dump 元素几何匹配（中心点包含 + 最小面积）
 * 目录：tests/shared/p0/
 *
 * 覆盖：嵌套容器选最具体叶子元素 / 精确坐标全等兼容 / 零尺寸跳过 /
 *       一对一先到先得 / 未命中 / 边界闭区间命中。
 */
import { describe, expect, it } from 'vitest'
import { matchOcrToElements } from '@/shared/ocrMatch'

describe('[P0] shared/ocrMatch', () => {
  it('嵌套容器：同一 OCR 中心点落在多层 bounds 内，选面积最小元素', () => {
    const elements = [
      { x: 0, y: 0, width: 1440, height: 2872 }, // 整屏容器
      { x: 0, y: 110, width: 1440, height: 321 }, // viewBarrier
      { x: 77, y: 110, width: 144, height: 211 }, // tvTabLayout（最具体）
    ]
    const texts = [{ text: '设备', x: 64, y: 170, width: 169, height: 96 }]

    const { byElement, matchedOcrIndexes } = matchOcrToElements(elements, texts)

    expect(byElement.get(2)).toBe(texts[0])
    expect(byElement.get(0)).toBeUndefined()
    expect(byElement.get(1)).toBeUndefined()
    expect(matchedOcrIndexes.has(0)).toBe(true)
  })

  it('精确坐标全等：中心点落在元素内，仍可命中（兼容旧口径边界）', () => {
    const elements = [{ x: 0, y: 0, width: 100, height: 100 }]
    const texts = [{ text: 't', x: 0, y: 0, width: 100, height: 100 }]

    const { byElement } = matchOcrToElements(elements, texts)

    expect(byElement.get(0)).toBe(texts[0])
  })

  it('零尺寸元素被跳过，不参与匹配', () => {
    const elements = [
      { x: 0, y: 0, width: 0, height: 0 },
      { x: 0, y: 0, width: 100, height: 100 },
    ]
    const texts = [{ text: 't', x: 10, y: 10, width: 20, height: 20 }]

    const { byElement, matchedOcrIndexes } = matchOcrToElements(elements, texts)

    expect(byElement.get(0)).toBeUndefined()
    expect(byElement.get(1)).toBe(texts[0])
    expect(matchedOcrIndexes.has(0)).toBe(true)
  })

  it('一对一：同一元素被多条 OCR 命中时先到先得，后续 OCR 视为未匹配', () => {
    const elements = [{ x: 0, y: 0, width: 100, height: 100 }]
    const texts = [
      { text: 'a', x: 10, y: 10, width: 10, height: 10 },
      { text: 'b', x: 50, y: 50, width: 10, height: 10 },
    ]

    const { byElement, matchedOcrIndexes } = matchOcrToElements(elements, texts)

    expect(byElement.get(0)).toBe(texts[0])
    expect(matchedOcrIndexes.has(0)).toBe(true)
    expect(matchedOcrIndexes.has(1)).toBe(false)
  })

  it('未命中：OCR 中心点不落在任何元素 bounds 内 → 无匹配', () => {
    const elements = [{ x: 0, y: 0, width: 50, height: 50 }]
    const texts = [{ text: 't', x: 100, y: 100, width: 10, height: 10 }]

    const { byElement, matchedOcrIndexes } = matchOcrToElements(elements, texts)

    expect(byElement.size).toBe(0)
    expect(matchedOcrIndexes.size).toBe(0)
  })

  it('边界：OCR 中心点恰在元素边界上，闭区间仍命中', () => {
    const elements = [{ x: 0, y: 0, width: 100, height: 100 }]
    const texts = [{ text: 't', x: 50, y: 50, width: 100, height: 100 }] // 中心 (100,100)

    const { byElement } = matchOcrToElements(elements, texts)

    expect(byElement.get(0)).toBe(texts[0])
  })
})
