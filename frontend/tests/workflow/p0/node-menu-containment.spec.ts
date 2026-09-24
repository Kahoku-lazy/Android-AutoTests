/**
 * [P0] 必测 — 画布右键菜单（含「选择 Android 页面」列表）不出屏
 * （spec: page-flow-overlay-containment）
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `page-flow-canvas-cursor-anchoring` 的浮层边界契约：
 *  1. 锚点在屏内时保持光标锚定位置；
 *  2. 锚点落在右下角外时，菜单左/上边缘收进视口（保留 8px 边距），不是被裁切；
 *  3. 切到「选择 Android 页面」列表后仍在屏内，搜索框可见；
 *  4. 仍是光标锚定的非模态菜单：不出现全屏遮罩，也不居中。
 *
 * jsdom 的 getBoundingClientRect 恒为 0，因此贴边用浮层常量尺寸（与 CSS 宽度一致）；
 * 真实浏览器下的实测尺寸精修由浏览器实测（tasks 3.3）覆盖。
 */
import { mount, flushPromises } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"

import NodeContextMenu from "@/modules/workflow/components/vueflow/NodeContextMenu.vue"
import EdgeContextMenu from "@/modules/workflow/components/vueflow/EdgeContextMenu.vue"
import {
  EDGE_MENU_SIZE,
  NODE_MENU_SIZE,
  OVERLAY_MARGIN,
} from "@/modules/workflow/helpers/overlayPosition"

vi.mock("@/modules/workflow/data/pageCatalog", () => ({
  fetchCatalogPages: vi.fn().mockResolvedValue({ pages: [], source: "api", message: "" }),
}))

/** 与浮层定位读到的视口同源（jsdom 默认 1024×768） */
const VIEWPORT = { width: window.innerWidth, height: window.innerHeight }

function mountMenu(x: number, y: number) {
  return mount(NodeContextMenu, {
    props: {
      show: true,
      x,
      y,
      nodeId: "n1",
      nodeLabel: "页面1",
      canLinkPage: true,
    },
    global: { stubs: { teleport: true } },
  })
}

/** 从浮层根元素的 style 里读 left / top（px） */
function stylePosition(el: Element) {
  const style = el.getAttribute("style") || ""
  const left = /left:\s*(-?\d+(?:\.\d+)?)px/.exec(style)
  const top = /top:\s*(-?\d+(?:\.\d+)?)px/.exec(style)
  if (!left || !top) throw new Error(`浮层样式里读不到 left/top: ${style}`)
  return { left: Number(left[1]), top: Number(top[1]) }
}

function menuPosition(wrapper: ReturnType<typeof mountMenu>) {
  return stylePosition(wrapper.find(".node-menu").element)
}

describe("画布右键菜单 — 视口内完整可见", () => {
  it("锚点在屏内时保持光标位置", () => {
    const wrapper = mountMenu(100, 120)

    expect(menuPosition(wrapper)).toEqual({ left: 100, top: 120 })
  })

  it("锚点落在右下角外时收进视口并保留 8px 边距", () => {
    const wrapper = mountMenu(VIEWPORT.width + 200, VIEWPORT.height + 200)
    const { left, top } = menuPosition(wrapper)

    expect(left).toBe(VIEWPORT.width - NODE_MENU_SIZE.width - OVERLAY_MARGIN)
    expect(top).toBe(VIEWPORT.height - NODE_MENU_SIZE.height - OVERLAY_MARGIN)
    expect(left).toBeGreaterThanOrEqual(OVERLAY_MARGIN)
    expect(top).toBeGreaterThanOrEqual(OVERLAY_MARGIN)
  })

  it("靠近右缘时右边缘不超出视口，菜单项全部渲染", () => {
    const wrapper = mountMenu(VIEWPORT.width - 10, 200)
    const { left } = menuPosition(wrapper)

    expect(left + NODE_MENU_SIZE.width).toBeLessThanOrEqual(VIEWPORT.width - OVERLAY_MARGIN)
    expect(wrapper.find(".menu-item").exists()).toBe(true)
    expect(wrapper.text()).toContain("关联 Android 页面")
    expect(wrapper.text()).toContain("删除节点")
  })

  it("切到「选择 Android 页面」列表后仍在屏内，搜索框可见", async () => {
    const wrapper = mountMenu(VIEWPORT.width - 10, VIEWPORT.height - 10)

    await wrapper.find(".menu-item").trigger("click")
    await flushPromises()

    const { left, top } = menuPosition(wrapper)
    expect(left + NODE_MENU_SIZE.width).toBeLessThanOrEqual(VIEWPORT.width - OVERLAY_MARGIN)
    expect(top + NODE_MENU_SIZE.height).toBeLessThanOrEqual(VIEWPORT.height - OVERLAY_MARGIN)
    expect(wrapper.find("input.search").exists()).toBe(true)
    expect(wrapper.find(".list").exists()).toBe(true)
  })

  it("仍是光标锚定的非模态菜单：无全屏遮罩、不居中", () => {
    const wrapper = mountMenu(600, 300)
    const { left } = menuPosition(wrapper)

    expect(wrapper.find(".el-overlay").exists()).toBe(false)
    expect(wrapper.find(".node-menu-backdrop").exists()).toBe(false)
    expect(left).toBe(600)
    expect(left).not.toBe((VIEWPORT.width - NODE_MENU_SIZE.width) / 2)
  })
})

describe("画布连线右键菜单 — 视口内完整可见", () => {
  function mountEdgeMenu(x: number, y: number) {
    return mount(EdgeContextMenu, {
      props: { show: true, x, y, linkId: 3, label: "入口", customName: "" },
      global: { stubs: { teleport: true } },
    })
  }

  it("锚点落在右下角外时收进视口并保留 8px 边距", () => {
    const wrapper = mountEdgeMenu(VIEWPORT.width + 100, VIEWPORT.height + 100)
    const { left, top } = stylePosition(wrapper.find(".edge-menu").element)

    expect(left).toBe(VIEWPORT.width - EDGE_MENU_SIZE.width - OVERLAY_MARGIN)
    expect(top).toBe(VIEWPORT.height - EDGE_MENU_SIZE.height - OVERLAY_MARGIN)
    expect(wrapper.text()).toContain("重命名连线")
    expect(wrapper.text()).toContain("删除连线")
  })

  it("重命名态仍在屏内", async () => {
    const wrapper = mountEdgeMenu(VIEWPORT.width - 4, VIEWPORT.height - 4)

    await wrapper.findAll(".edge-menu__item")[0].trigger("click")
    await flushPromises()

    const { left, top } = stylePosition(wrapper.find(".edge-menu").element)
    expect(left + EDGE_MENU_SIZE.width).toBeLessThanOrEqual(VIEWPORT.width - OVERLAY_MARGIN)
    expect(top + EDGE_MENU_SIZE.height).toBeLessThanOrEqual(VIEWPORT.height - OVERLAY_MARGIN)
    expect(wrapper.find("input.edge-menu__input").exists()).toBe(true)
  })
})
