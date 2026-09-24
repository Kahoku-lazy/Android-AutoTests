/**
 * [P0] 必测 — 新建页面节点落在鼠标处（组件接线，spec: page-flow-node-placement）
 * 目录：tests/workflow/p0/
 *
 * 落点数学由 `canvas-placement.spec.ts` 覆盖；这里只验组件接线：
 *  1. 鼠标最后停留处 → 节点中心；
 *  2. 鼠标未进过画布 → 画布可视区域中心；
 *  3. 同一位置连续新建做最小错位；
 *  4. 命名与既有节点坐标不受影响。
 *
 * jsdom 无布局：给画布容器与 VueFlow 根元素各塞一个确定矩形，视口变换由 `getViewport` mock 给出。
 */
import { createPinia, setActivePinia } from "pinia"
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"

import PageFlowVueFlow from "@/modules/workflow/components/vueflow/PageFlowVueFlow.vue"
import { useWorkflowStore } from "@/modules/workflow/stores/workflowStore"
import {
  clientToFlowPoint,
  flowPointToNodePos,
  STACK_STEP,
} from "@/modules/workflow/helpers/canvasPlacement"
import type { WorkflowNode } from "@/modules/workflow/types/workflow"

/** 画布可视区域（jsdom 无布局：给画布元素一个确定矩形） */
const CANVAS_RECT = { left: 100, top: 50, width: 900, height: 600 }
/** VueFlow 根元素原点与视口变换 */
const FLOW_ORIGIN = { left: 120, top: 70 }
const VIEWPORT = { x: 40, y: 25, zoom: 2 }

vi.mock("@vue-flow/core", () => ({
  VueFlow: { name: "VueFlow", setup: () => () => null },
  ConnectionMode: { Loose: "loose" },
  Position: { Left: "left", Right: "right", Top: "top", Bottom: "bottom" },
  Handle: { name: "Handle", setup: () => () => null },
  useVueFlow: () => ({
    onConnect: vi.fn(),
    onNodeDragStop: vi.fn(),
    onEdgesChange: vi.fn(),
    onEdgeContextMenu: vi.fn(),
    fitView: vi.fn(),
    updateNodeInternals: vi.fn(),
    getViewport: () => ({ ...VIEWPORT }),
    // 测试环境没有 VueFlow 内部节点表：走「无实测尺寸」的估算 + 渲染后定稿路径
    findNode: () => undefined,
  }),
}))
vi.mock("@vue-flow/background", () => ({
  Background: { name: "Background", setup: () => () => null },
}))
vi.mock("@vue-flow/controls", () => ({ Controls: { name: "Controls", setup: () => () => null } }))
vi.mock("@vue-flow/minimap", () => ({ MiniMap: { name: "MiniMap", setup: () => () => null } }))

function rectOf(box: { left: number; top: number; width: number; height: number }): DOMRect {
  return {
    ...box,
    right: box.left + box.width,
    bottom: box.top + box.height,
    x: box.left,
    y: box.top,
    toJSON: () => ({}),
  } as DOMRect
}

async function mountCanvas() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(PageFlowVueFlow, {
    props: { seedDemo: false },
    global: { plugins: [pinia] },
  })
  await flushPromises()

  const canvas = wrapper.find(".vf-canvas").element as HTMLElement
  canvas.getBoundingClientRect = () => rectOf(CANVAS_RECT)
  // VueFlow 根元素（真实环境由 @vue-flow/core 渲染，测试中被 mock 掉，这里手工放一个）
  const flowRoot = document.createElement("div")
  flowRoot.className = "vue-flow"
  flowRoot.getBoundingClientRect = () => rectOf({ ...FLOW_ORIGIN, width: 0, height: 0 })
  canvas.appendChild(flowRoot)

  return { wrapper, store: useWorkflowStore() }
}

async function moveMouseTo(wrapper: VueWrapper, x: number, y: number) {
  await wrapper.find(".vf-canvas").trigger("mousemove", { clientX: x, clientY: y })
}

async function clickAddPage(wrapper: VueWrapper) {
  await wrapper
    .findAll(".vf-actions button")
    .find((b) => b.text().includes("+ 页面"))!
    .trigger("click")
  await flushPromises()
}

/** 组件落点规则：参照点画布坐标 − 估算尺寸的一半 */
function expectedPos(
  store: ReturnType<typeof useWorkflowStore>,
  node: WorkflowNode,
  client: { x: number; y: number },
) {
  const center = clientToFlowPoint(client, FLOW_ORIGIN, VIEWPORT)!
  return flowPointToNodePos(center, {
    width: node.size[0] || 180,
    height: store.computeNodeHeight(node),
  })
}

describe("新建页面节点 — 落点跟随鼠标", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("节点中心落在鼠标最后停留的位置", async () => {
    const { wrapper, store } = await mountCanvas()

    await moveMouseTo(wrapper, 640, 420)
    await clickAddPage(wrapper)

    const node = store.pageNodes[0]
    const expected = expectedPos(store, node, { x: 640, y: 420 })
    expect(store.pageNodes).toHaveLength(1)
    expect(node.pos[0]).toBeCloseTo(expected[0], 6)
    expect(node.pos[1]).toBeCloseTo(expected[1], 6)
    wrapper.unmount()
  })

  it("鼠标移动多次时以最后一次停留为准", async () => {
    const { wrapper, store } = await mountCanvas()

    await moveMouseTo(wrapper, 300, 300)
    await moveMouseTo(wrapper, 700, 500)
    await clickAddPage(wrapper)

    const node = store.pageNodes[0]
    const expected = expectedPos(store, node, { x: 700, y: 500 })
    expect(node.pos[0]).toBeCloseTo(expected[0], 6)
    expect(node.pos[1]).toBeCloseTo(expected[1], 6)
    wrapper.unmount()
  })

  it("鼠标未进过画布时落到画布可视区域中心", async () => {
    const { wrapper, store } = await mountCanvas()

    await clickAddPage(wrapper)

    const node = store.pageNodes[0]
    const centerClient = {
      x: CANVAS_RECT.left + CANVAS_RECT.width / 2,
      y: CANVAS_RECT.top + CANVAS_RECT.height / 2,
    }
    const expected = expectedPos(store, node, centerClient)
    expect(node.pos[0]).toBeCloseTo(expected[0], 6)
    expect(node.pos[1]).toBeCloseTo(expected[1], 6)
    wrapper.unmount()
  })

  it("不动鼠标连点两次时两个节点不重合", async () => {
    const { wrapper, store } = await mountCanvas()

    await moveMouseTo(wrapper, 500, 400)
    await clickAddPage(wrapper)
    await clickAddPage(wrapper)

    const [first, second] = store.pageNodes
    expect(store.pageNodes).toHaveLength(2)
    expect(second.pos).not.toEqual(first.pos)
    expect(Math.abs(second.pos[0] - first.pos[0])).toBeCloseTo(STACK_STEP[0], 6)
    expect(Math.abs(second.pos[1] - first.pos[1])).toBeCloseTo(STACK_STEP[1], 6)
    wrapper.unmount()
  })

  it("落点只影响新节点：命名沿用「页面N」，既有节点坐标不变", async () => {
    const { wrapper, store } = await mountCanvas()

    await moveMouseTo(wrapper, 400, 300)
    await clickAddPage(wrapper)
    const firstPos = [...store.pageNodes[0].pos] as [number, number]

    await moveMouseTo(wrapper, 800, 300)
    await clickAddPage(wrapper)

    expect(store.pageNodes[0].pos).toEqual(firstPos)
    expect(store.pageNodes.map((n) => n.widgets_values[0])).toEqual(["页面1", "页面2"])
    wrapper.unmount()
  })
})
