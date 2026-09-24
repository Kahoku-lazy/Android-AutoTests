/**
 * [P0] 必测 — 画布落点换算（spec: page-flow-node-placement）
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `page-flow-canvas-cursor-anchoring` 的落点数学：
 *  1. 屏幕坐标 → 画布坐标：带平移与缩放，且**不做 16px 网格吸附**（1px 屏幕位移必须有非零画布位移）；
 *  2. 节点中心落在目标画布点上；
 *  3. 同一落点已被占用时按 (24,16) 步长错位，最多 8 步。
 */
import { describe, expect, it } from "vitest"

import {
  clientToFlowPoint,
  flowPointToNodePos,
  STACK_MAX_STEPS,
  STACK_STEP,
  stackingOffset,
} from "@/modules/workflow/helpers/canvasPlacement"

const ORIGIN = { left: 100, top: 50 }

describe("画布落点换算 — 纯函数", () => {
  it("缩放 1、无平移时屏幕坐标即画布坐标", () => {
    const flow = clientToFlowPoint({ x: 340, y: 250 }, ORIGIN, { x: 0, y: 0, zoom: 1 })

    expect(flow).toEqual({ x: 240, y: 200 })
  })

  it("带上平移与缩放", () => {
    const flow = clientToFlowPoint({ x: 340, y: 250 }, ORIGIN, { x: 40, y: 20, zoom: 2 })

    expect(flow).toEqual({ x: 100, y: 90 })
  })

  it("不做网格吸附：1px 屏幕位移对应非零画布位移", () => {
    const viewport = { x: 353.5, y: 186.5, zoom: 2.5 }
    const base = clientToFlowPoint({ x: 820, y: 542 }, ORIGIN, viewport)!
    const moved = clientToFlowPoint({ x: 821, y: 543 }, ORIGIN, viewport)!

    expect(moved.x - base.x).toBeCloseTo(1 / 2.5, 6)
    expect(moved.y - base.y).toBeCloseTo(1 / 2.5, 6)
    expect(moved.x - base.x).not.toBe(0)
  })

  it("缩放为 0（视口未初始化）时返回 null，由调用方兜底", () => {
    expect(clientToFlowPoint({ x: 10, y: 10 }, ORIGIN, { x: 0, y: 0, zoom: 0 })).toBeNull()
  })

  it("节点中心落在目标点上", () => {
    const pos = flowPointToNodePos({ x: 300, y: 200 }, { width: 180, height: 82 })

    expect(pos).toEqual([210, 159])
    expect(pos[0] + 180 / 2).toBe(300)
    expect(pos[1] + 82 / 2).toBe(200)
  })
})

describe("同一位置连续新建 — 最小错位（按节点中心）", () => {
  it("落点空闲时不偏移", () => {
    expect(stackingOffset({ x: 100, y: 100 }, [{ x: 400, y: 400 }])).toEqual({ x: 100, y: 100 })
  })

  it("落点已被占用时按步长错位一次", () => {
    const center = { x: 100, y: 100 }
    const stacked = stackingOffset(center, [center])

    expect(stacked).toEqual({ x: 100 + STACK_STEP[0], y: 100 + STACK_STEP[1] })
  })

  it("连续占用时逐级错位，最多 8 步", () => {
    const occupied = Array.from({ length: 20 }, (_, i) => ({
      x: 100 + i * STACK_STEP[0],
      y: 100 + i * STACK_STEP[1],
    }))

    const stacked = stackingOffset({ x: 100, y: 100 }, occupied)

    expect(stacked).toEqual({
      x: 100 + STACK_MAX_STEPS * STACK_STEP[0],
      y: 100 + STACK_MAX_STEPS * STACK_STEP[1],
    })
  })
})
