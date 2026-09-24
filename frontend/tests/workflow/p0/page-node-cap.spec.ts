/**
 * [P0] 必测 — 页面流画布节点数量上限（spec: page-flow-node-cap）
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `raise-page-node-cap` 的容量契约：
 *  1. 页面节点上限 50：第 50 个可建，第 51 个被拒且画布构成不变；
 *  2. 顶格时工具栏出现含上限数值的提示（不得静默无反应）；
 *  3. 起点 1 / 终点 5 / 弹窗不限 三条边界不随页面节点上限调整而变；
 *  4. 页面节点已超限的存量文档全量保留、可删可存（上限只拦新增）。
 *
 * 画布组件挂载时把 Vue Flow 整体 mock 掉：本用例只关心工具栏与 store 的
 * 上限行为，不测画布渲染；真实用例在浏览器实测（tasks 3.2）。
 */
import { createPinia, setActivePinia, type Pinia } from "pinia"
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { NODE_REGISTRY } from "@/modules/workflow/registry/nodeRegistry"
import { useWorkflowStore } from "@/modules/workflow/stores/workflowStore"
import type { WorkflowNode, WorkflowSaveData } from "@/modules/workflow/types/workflow"
// 静态导入：画布组件拉入 element-plus，动态 import 会把首次转换成本算进用例超时
import PageFlowVueFlow from "@/modules/workflow/components/vueflow/PageFlowVueFlow.vue"

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
    getViewport: () => ({ x: 0, y: 0, zoom: 1 }),
    findNode: () => undefined,
  }),
}))
vi.mock("@vue-flow/background", () => ({
  Background: { name: "Background", setup: () => () => null },
}))
vi.mock("@vue-flow/controls", () => ({ Controls: { name: "Controls", setup: () => () => null } }))
vi.mock("@vue-flow/minimap", () => ({ MiniMap: { name: "MiniMap", setup: () => () => null } }))

/** 上限真相源：注册表。用例断言它，改值必须同时改用例 */
const PAGE_CAP = 50
/** 起点 / 终点的既有边界（本变更不改动，锁死防回归） */
const START_CAP = 1
const END_CAP = 5

function pageNode(index: number): WorkflowNode {
  return {
    id: `n${index}`,
    type: "PageNode",
    pos: [0, 0],
    size: [180, 0],
    category: "page",
    inputs: [{ name: "入口", type: "entry", slot_index: 0, link: null, links: [] }],
    outputs: [],
    widgets_values: [`页面${index}`, "teal"],
    properties: {},
  }
}

/** 一篇含 count 个页面节点的文档快照（对齐服务端 config_json 的 {nodes, links}） */
function snapshotWithPages(count: number): WorkflowSaveData {
  return {
    name: "H6810设备页面关系流",
    version: "1.0",
    savedAt: "2026-09-24T00:00:00.000Z",
    nodes: Array.from({ length: count }, (_, i) => pageNode(i + 1)),
    links: [],
  }
}

/** 挂载画布组件：pinia 与用例内 store 必须是同一个实例 */
async function mountCanvas(pinia: Pinia): Promise<VueWrapper> {
  return mount(PageFlowVueFlow, {
    props: { seedDemo: false },
    global: { plugins: [pinia] },
  })
}

/** 工具栏按钮按可见文案定位（同文案按钮唯一） */
function toolbarButton(wrapper: VueWrapper, label: string) {
  const btn = wrapper.findAll("button").find((b) => b.text().includes(label))
  if (!btn) throw new Error(`工具栏未找到按钮：${label}`)
  return btn
}

describe("页面流节点上限 — 注册表与 store", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("页面节点上限为 50", () => {
    expect(NODE_REGISTRY.PageNode.maxInstances).toBe(PAGE_CAP)
  })

  it("第 50 个页面节点可创建，第 51 个被拒且提示含上限", () => {
    const store = useWorkflowStore()
    store.applySnapshot(snapshotWithPages(PAGE_CAP - 1))

    expect(store.createNode("PageNode", 0, 0)).not.toBeNull()
    expect(store.pageNodes).toHaveLength(PAGE_CAP)

    expect(store.createNode("PageNode", 0, 0)).toBeNull()
    expect(store.pageNodes).toHaveLength(PAGE_CAP)
    expect(store.statusMessage).toContain(String(PAGE_CAP))
  })

  it("起点仍最多 1 个、终点仍最多 5 个、弹窗不限", () => {
    const store = useWorkflowStore()

    for (let i = 0; i < START_CAP; i++) {
      expect(store.createNode("StartNode", 0, 0)).not.toBeNull()
    }
    expect(store.startNodes).toHaveLength(START_CAP)
    expect(store.createNode("StartNode", 0, 0)).toBeNull()
    expect(store.startNodes).toHaveLength(START_CAP)

    for (let i = 0; i < END_CAP; i++) {
      expect(store.createNode("EndNode", 0, 0)).not.toBeNull()
    }
    expect(store.endNodes).toHaveLength(END_CAP)
    expect(store.createNode("EndNode", 0, 0)).toBeNull()
    expect(store.endNodes).toHaveLength(END_CAP)

    for (let i = 0; i < END_CAP + 3; i++) {
      expect(store.createNode("PopupNode", 0, 0)).not.toBeNull()
    }
    expect(store.popupNodes).toHaveLength(END_CAP + 3)
  })

  it("超限存量文档（60 个页面节点）全量保留、可删可存", () => {
    const store = useWorkflowStore()
    store.applySnapshot(snapshotWithPages(60))

    expect(store.pageNodes).toHaveLength(60)

    store.removeNode(store.pageNodes[0].id)
    expect(store.pageNodes).toHaveLength(59)

    const saved = store.snapshotGraph("H6810设备页面关系流")
    expect(saved.nodes.filter((n) => n.type === "PageNode")).toHaveLength(59)
  })
})

describe("页面流节点上限 — 画布工具栏反馈", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("未顶格时点「+ 页面」正常新增，连点到顶格后再点才出现含 50 的提示", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useWorkflowStore()
    store.applySnapshot(snapshotWithPages(1))

    const wrapper = await mountCanvas(pinia)
    await flushPromises()

    // 已有 1 个，连点 49 次到顶格
    const addPage = toolbarButton(wrapper, "+ 页面")
    for (let i = 0; i < PAGE_CAP - 1; i++) {
      await addPage.trigger("click")
    }
    await flushPromises()

    expect(store.pageNodes).toHaveLength(PAGE_CAP)
    expect(wrapper.find(".hint").exists()).toBe(false)

    await addPage.trigger("click")
    await flushPromises()

    expect(store.pageNodes).toHaveLength(PAGE_CAP)
    const hint = wrapper.find(".hint")
    expect(hint.exists()).toBe(true)
    expect(hint.text()).toContain(String(PAGE_CAP))
    wrapper.unmount()
  })

  it("打开已是 50 个页面节点的文档，点「+ 页面」不新增且给出提示", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useWorkflowStore()
    store.applySnapshot(snapshotWithPages(PAGE_CAP))

    const wrapper = await mountCanvas(pinia)
    await flushPromises()
    expect(store.pageNodes).toHaveLength(PAGE_CAP)

    await toolbarButton(wrapper, "+ 页面").trigger("click")
    await flushPromises()

    expect(store.pageNodes).toHaveLength(PAGE_CAP)
    const hint = wrapper.find(".hint")
    expect(hint.exists()).toBe(true)
    expect(hint.text()).toContain(String(PAGE_CAP))
    wrapper.unmount()
  })
})
