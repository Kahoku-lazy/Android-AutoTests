/**
 * [P0] 必测 — 光标锚定浮层的视口收敛（spec: page-flow-overlay-containment）
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `page-flow-canvas-cursor-anchoring` 的浮层边界契约：
 *  1. 锚点在屏内时位置不变；越界时向屏内平移并保留 8px 边距；
 *  2. 浮层比视口还大时贴到 8px（不是负坐标），交由 CSS 的 max-height 收敛；
 *  3. 实测尺寸不可用（0）时回落到各浮层的常量尺寸。
 */
import { describe, expect, it } from "vitest"

import {
  containOverlayPosition,
  currentViewport,
  EDGE_MENU_SIZE,
  ELEMENT_PICKER_SIZE,
  measuredOrFallback,
  NODE_MENU_SIZE,
  OVERLAY_MARGIN,
} from "@/modules/workflow/helpers/overlayPosition"

const VIEWPORT = { width: 1280, height: 800 }

describe("浮层视口收敛 — 纯函数", () => {
  it("锚点在屏内且放得下时位置不变", () => {
    expect(containOverlayPosition({ x: 200, y: 150 }, NODE_MENU_SIZE, VIEWPORT)).toEqual({
      x: 200,
      y: 150,
    })
  })

  it("右侧越界时向左平移，右边缘保留 8px 边距", () => {
    const pos = containOverlayPosition({ x: 1240, y: 100 }, NODE_MENU_SIZE, VIEWPORT)

    expect(pos.x).toBe(VIEWPORT.width - NODE_MENU_SIZE.width - OVERLAY_MARGIN)
    expect(pos.x + NODE_MENU_SIZE.width).toBeLessThanOrEqual(VIEWPORT.width - OVERLAY_MARGIN)
    expect(pos.y).toBe(100)
  })

  it("下侧越界时向上平移，下边缘保留 8px 边距", () => {
    const pos = containOverlayPosition({ x: 300, y: 790 }, NODE_MENU_SIZE, VIEWPORT)

    expect(pos.y).toBe(VIEWPORT.height - NODE_MENU_SIZE.height - OVERLAY_MARGIN)
    expect(pos.y + NODE_MENU_SIZE.height).toBeLessThanOrEqual(VIEWPORT.height - OVERLAY_MARGIN)
    expect(pos.x).toBe(300)
  })

  it("右下角同时越界时两个方向都收进屏内", () => {
    const pos = containOverlayPosition({ x: 1270, y: 795 }, EDGE_MENU_SIZE, VIEWPORT)

    expect(pos.x + EDGE_MENU_SIZE.width).toBeLessThanOrEqual(VIEWPORT.width - OVERLAY_MARGIN)
    expect(pos.y + EDGE_MENU_SIZE.height).toBeLessThanOrEqual(VIEWPORT.height - OVERLAY_MARGIN)
    expect(pos.x).toBeGreaterThanOrEqual(OVERLAY_MARGIN)
    expect(pos.y).toBeGreaterThanOrEqual(OVERLAY_MARGIN)
  })

  it("浮层比视口还大时贴到 8px（不是负坐标）", () => {
    const pos = containOverlayPosition(
      { x: 500, y: 500 },
      { width: 600, height: 900 },
      { width: 480, height: 700 },
    )

    expect(pos).toEqual({ x: OVERLAY_MARGIN, y: OVERLAY_MARGIN })
  })

  it("实测尺寸为 0 时回落常量，只为 0 的那一边回落", () => {
    expect(measuredOrFallback({ width: 0, height: 0 }, NODE_MENU_SIZE)).toEqual(NODE_MENU_SIZE)
    expect(measuredOrFallback({ width: 300, height: 0 }, NODE_MENU_SIZE)).toEqual({
      width: 300,
      height: NODE_MENU_SIZE.height,
    })
  })

  it("三个浮层的兜底尺寸与其 CSS 宽度一致", () => {
    expect(NODE_MENU_SIZE.width).toBe(288)
    expect(EDGE_MENU_SIZE.width).toBe(248)
    expect(ELEMENT_PICKER_SIZE.width).toBe(340)
  })

  it("视口尺寸取当前窗口（jsdom 下为可读的正数）", () => {
    const viewport = currentViewport()

    expect(viewport.width).toBeGreaterThan(0)
    expect(viewport.height).toBeGreaterThan(0)
  })
})
