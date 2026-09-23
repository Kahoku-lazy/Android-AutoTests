/**
 * [P0] 必测 — 截图画布几何纯函数（框归一化 + 命中取舍）
 * 目录：tests/device-inspector/p0/
 *
 * 从 ScreenshotView.vue 抽出，锁定改动前的行为：三形态坐标、面积最小者取胜、
 * 零尺寸不参与、框外无命中。
 */
import { describe, expect, it } from 'vitest'
import { boxOf, pickElementAt } from '@/modules/device-inspector/helpers/screenshotGeometry'

describe('[P0] screenshotGeometry.boxOf', () => {
  it('coords 形态（分层接口）优先于其它字段', () => {
    expect(boxOf({ coords: { x: 1, y: 2, w: 30, h: 40 }, x: 999, y: 999, width: 1, height: 1 })).toEqual({
      x: 1,
      y: 2,
      w: 30,
      h: 40,
    })
  })

  it('x/y/width/height 形态（旧响应）', () => {
    expect(boxOf({ x: 10, y: 20, width: 100, height: 200 })).toEqual({ x: 10, y: 20, w: 100, h: 200 })
  })

  it('bounds 文本形态：[x1,y1][x2,y2] 换算成左上角与宽高', () => {
    expect(boxOf({ bounds: '[10,20][110,220]' })).toEqual({ x: 10, y: 20, w: 100, h: 200 })
  })

  it('bounds 缺失或非法时不产矩形', () => {
    expect(boxOf({ bounds: 'nope' })).toBeNull()
    expect(boxOf({ x: 1, y: 2, width: 3 })).toBeNull()
    expect(boxOf({})).toBeNull()
    expect(boxOf(null)).toBeNull()
  })

  it('coords 不完整时回退到 x/y/width/height', () => {
    expect(boxOf({ coords: { x: 1, y: 2 }, x: 5, y: 6, width: 7, height: 8 })).toEqual({
      x: 5,
      y: 6,
      w: 7,
      h: 8,
    })
  })
})

describe('[P0] screenshotGeometry.pickElementAt', () => {
  const outer = { name: 'outer', coords: { x: 0, y: 0, w: 1440, h: 2872 } }
  const card = { name: 'card', coords: { x: 0, y: 100, w: 1440, h: 320 } }
  const leaf = { name: 'leaf', coords: { x: 77, y: 110, w: 144, h: 211 } }

  it('嵌套框：命中包含该点且面积最小的元素', () => {
    expect(pickElementAt([outer, card, leaf], 100, 200)).toBe(leaf)
    expect(pickElementAt([outer, card, leaf], 1000, 1000)).toBe(outer)
  })

  it('框的四边是闭区间（边界上仍命中）', () => {
    expect(pickElementAt([card], 0, 100)).toBe(card)
    expect(pickElementAt([card], 1440, 420)).toBe(card)
  })

  it('框外无命中时返回 null', () => {
    expect(pickElementAt([card], 0, 99)).toBeNull()
    expect(pickElementAt([], 0, 0)).toBeNull()
  })

  it('宽或高为 0 的条目不参与命中（框不可见）', () => {
    const zero = { name: 'zero', coords: { x: 0, y: 0, w: 0, h: 100 } }
    expect(pickElementAt([zero], 0, 50)).toBeNull()
    expect(pickElementAt([zero, card], 0, 200)).toBe(card)
  })

  it('坐标非法的条目被跳过，不影响其它条目的命中', () => {
    const broken = { name: 'broken', bounds: 'oops' }
    expect(pickElementAt([broken, card], 100, 200)).toBe(card)
  })
})
