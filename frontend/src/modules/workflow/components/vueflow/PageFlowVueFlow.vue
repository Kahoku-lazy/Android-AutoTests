<script setup lang="ts">
import { ref, computed, watch, provide, onMounted, onUnmounted, markRaw, nextTick } from "vue"
import { ElMessageBox } from "element-plus"
import { VueFlow, useVueFlow, ConnectionMode } from "@vue-flow/core"
import { Background } from "@vue-flow/background"
import { Controls } from "@vue-flow/controls"
import { MiniMap } from "@vue-flow/minimap"
import type { Connection, NodeMouseEvent, EdgeMouseEvent } from "@vue-flow/core"
import { useWorkflowStore } from "@/modules/workflow/stores/workflowStore"
import {
  toVueFlowNodes,
  toVueFlowEdges,
  explainConnection,
  applyVueFlowConnect,
  syncNodePositionFromVueFlow,
  ensureWorkflowSeed,
} from "@/modules/workflow/composables/useVueFlowAdapter"
import PageFlowNode from "./PageFlowNode.vue"
import NodeContextMenu from "./NodeContextMenu.vue"
import EdgeContextMenu from "./EdgeContextMenu.vue"
import { PAGE_ELEMENTS, POPUP_ELEMENTS, ELEMENT_ICONS } from "@/modules/workflow/types/workflow"
import type { WorkflowNode } from "@/modules/workflow/types/workflow"
import { NODE_REGISTRY } from "@/modules/workflow/registry/nodeRegistry"
import { NODE_TYPES, NODE_TYPE_LABELS, type FlowDocType } from "@/modules/workflow/constants"
import { ELEMENT_PICKER_SIZE } from "@/modules/workflow/helpers/overlayPosition"
import {
  clientToFlowPoint,
  flowPointToNodePos,
  stackingOffset,
  type NodeSize,
} from "@/modules/workflow/helpers/canvasPlacement"
import { useContainedOverlay } from "@/modules/workflow/composables/useContainedOverlay"

/** 元素卡片 xpath 展示 — 兼容可选字段 */
function elXpath(el: { xpath?: string; type: string }): string {
  return el.xpath || el.type
}
import type { CatalogPage } from "@/modules/workflow/data/pageCatalog"

import "@vue-flow/core/dist/style.css"
import "@vue-flow/core/dist/theme-default.css"
import "@vue-flow/controls/dist/style.css"
import "@vue-flow/minimap/dist/style.css"

const emit = defineEmits<{
  "update:docName": [name: string]
  "back": []
  "rename": []
}>()

const props = withDefaults(
  defineProps<{
    seedDemo?: boolean
    docName?: string
    docId?: string
    /** 页面流 / 接口流 — 决定工具栏与可添加节点 */
    flowKind?: FlowDocType
  }>(),
  { seedDemo: true, docName: "", docId: "", flowKind: NODE_TYPES.PAGE_FLOW },
)

const kindLabel = computed(() => NODE_TYPE_LABELS[props.flowKind] || "页面流")

const store = useWorkflowStore()
const {
  onConnect,
  onNodeDragStop,
  onEdgesChange,
  onEdgeContextMenu,
  fitView,
  updateNodeInternals,
  getViewport,
  findNode: findFlowNode,
} = useVueFlow()

const nodeTypes = { pageFlow: markRaw(PageFlowNode) }
const connectionMode = ConnectionMode.Loose

const nodes = ref(toVueFlowNodes(store))
const edges = ref(toVueFlowEdges(store))
const status = ref("")

const picker = ref({ show: false, nodeId: "", search: "", x: 200, y: 120 })
/** 元素选择器浮层：锚点固定，收敛保证不出屏 */
const {
  el: pickerRef,
  position: pickerPosition,
  place: placePicker,
} = useContainedOverlay(ELEMENT_PICKER_SIZE)

/** 画布根元素 + 鼠标最后停留位置（客户端坐标）：新建页面节点的落点来源 */
const canvasRef = ref<HTMLElement | null>(null)
const lastPointer = ref<{ x: number; y: number } | null>(null)

function onCanvasPointerMove(e: MouseEvent) {
  lastPointer.value = { x: e.clientX, y: e.clientY }
}

const ctxMenu = ref({
  show: false,
  x: 0,
  y: 0,
  nodeId: "",
  nodeLabel: "",
  canLinkPage: true,
  linkedPageId: undefined as string | undefined,
  linkedPageName: undefined as string | undefined,
})

const edgeMenu = ref({
  show: false,
  x: 0,
  y: 0,
  linkId: 0,
  label: "",
  customName: "",
})

function openNodeContext(e: MouseEvent | TouchEvent, nodeId: string) {
  e.preventDefault()
  const node = store.findNode(nodeId)
  if (!node) return
  store.select(nodeId)
  const clientX = "clientX" in e ? e.clientX : (e.touches?.[0]?.clientX ?? 0)
  const clientY = "clientY" in e ? e.clientY : (e.touches?.[0]?.clientY ?? 0)
  const canLink =
    node.type === "PageNode" ||
    node.type === "PopupNode" ||
    (node.type === "StartNode" && node.properties?.start_kind !== "app")
  ctxMenu.value = {
    show: true,
    x: clientX,
    y: clientY,
    nodeId,
    nodeLabel: node.widgets_values[0] || nodeId,
    canLinkPage: !!canLink,
    linkedPageId: node.properties?.linked_page_id as string | undefined,
    linkedPageName: node.properties?.linked_page_name as string | undefined,
  }
}

function onNodeContextMenu({ event, node }: NodeMouseEvent) {
  openNodeContext(event as MouseEvent, node.id)
}

function handleLinkPage(page: CatalogPage) {
  if (!ctxMenu.value.nodeId) return
  store.linkPage(ctxMenu.value.nodeId, page)
  refreshFromStore()
  status.value = store.statusMessage || `已关联「${page.name}」，请添加元素`
}

async function handleResyncPage() {
  if (!ctxMenu.value.nodeId) return
  const ok = await store.resyncLinkedPage(ctxMenu.value.nodeId)
  refreshFromStore()
  status.value = store.statusMessage || (ok ? "元素已刷新" : "刷新失败")
}

function handleDeleteFromCtx() {
  if (!ctxMenu.value.nodeId) return
  store.removeNode(ctxMenu.value.nodeId)
  refreshFromStore()
  status.value = "节点已删除"
}

async function refreshFromStore() {
  nodes.value = toVueFlowNodes(store)
  edges.value = toVueFlowEdges(store)
  await nextTick()
  const ids = store.nodes.map((n) => n.id)
  if (ids.length) updateNodeInternals(ids)
}

provide("vfOpenPicker", (nodeId: string) => {
  picker.value = { show: true, nodeId, search: "", x: 280, y: 140 }
  void placePicker({ x: picker.value.x, y: picker.value.y })
})

provide("vfRefresh", () => {
  refreshFromStore()
})

const pickerPool = computed(() => {
  const node = store.findNode(picker.value.nodeId)
  if (!node) return []

  const linked = node.properties?.linked_elements as typeof PAGE_ELEMENTS | undefined
  if (linked?.length) return linked
  return NODE_REGISTRY[node.type]?.elementPool === "popup" ? POPUP_ELEMENTS : PAGE_ELEMENTS
})

const filteredPicker = computed(() => {
  const q = picker.value.search.toLowerCase()
  const node = store.findNode(picker.value.nodeId)
  const used = new Set(node?.outputs.map((p) => p.el?.id).filter(Boolean))
  return pickerPool.value
    .filter((e) => !q || e.label.toLowerCase().includes(q) || e.type.includes(q))
    .map((e) => ({ ...e, used: used.has(e.id) }))
})

function selectElement(elId: string) {
  const item = filteredPicker.value.find((x) => x.id === elId)
  if (!item || item.used) return

  store.addPort(picker.value.nodeId, elId)
  picker.value.show = false
  refreshFromStore()
  status.value = "已添加端口: " + item.label
}

function isValidConnection(connection: Connection) {
  return explainConnection(store, connection).ok
}

onConnect((connection) => {
  const explained = explainConnection(store, connection)
  if (!explained.ok) {
    status.value = explained.reason
    return
  }
  const ok = applyVueFlowConnect(store, explained.normalized)
  if (ok) {
    refreshFromStore()
    status.value = "连线成功 ✓ navigation → entry"
  } else {
    status.value = store.statusMessage || "连线失败"
  }
})

onNodeDragStop(({ node }) => {
  syncNodePositionFromVueFlow(store, node.id, node.position)
})

onEdgesChange((changes) => {
  for (const ch of changes) {
    if (ch.type === "remove") {
      const edge = edges.value.find((e) => e.id === ch.id)
      const linkId = edge?.data?.linkId as number | undefined
      if (linkId != null) store.removeLink(linkId)
    }
  }
  setTimeout(() => refreshFromStore(), 0)
})

// 右键连线 → 重命名 / 删除菜单
onEdgeContextMenu(({ event, edge }) => {
  const linkId = edge.data?.linkId as number | undefined
  if (linkId == null) return
  event.preventDefault()
  const link = store.findLink(linkId)
  const origin = link ? store.findNode(link.origin_id) : undefined
  const clientX = "clientX" in event ? (event as MouseEvent).clientX : 0
  const clientY = "clientY" in event ? (event as MouseEvent).clientY : 0
  edgeMenu.value = {
    show: true,
    x: clientX,
    y: clientY,
    linkId,
    label: origin?.outputs[link?.origin_slot ?? 0]?.name || "连线",
    customName: link?.name || "",
  }
})

function handleEdgeRename(id: number, name: string) {
  store.renameLink(id, name)
  refreshFromStore()
  status.value = name ? `连线已重命名：${name}` : "连线名称已恢复默认"
  edgeMenu.value.show = false
}

function handleEdgeDelete(id: number) {
  const link = store.findLink(id)
  if (!link) return
  const origin = store.findNode(link.origin_id)
  const target = store.findNode(link.target_id)
  const fromLabel = origin?.widgets_values?.[0] || `Node#${link.origin_id}`
  const toLabel = target?.widgets_values?.[0] || `Node#${link.target_id}`
  store.removeLink(id)
  refreshFromStore()
  status.value = `已断开 ${fromLabel} → ${toLabel}`
  edgeMenu.value.show = false
}

/** 同一落点连续新建时的最小错位（避免新节点被已有节点完全压住） */
const PAGE_STACK_STEP: [number, number] = [24, 16]

/** 鼠标位置缺失时退到画布可视区域中心；画布还没尺寸时返回 null（再退阶梯位置） */
function canvasCenterClientPoint(): { x: number; y: number } | null {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect || rect.width <= 0 || rect.height <= 0) return null
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
}

/** 落点参照的客户端坐标：鼠标最后停留处 → 画布可视区域中心 */
function dropClientPoint(): { x: number; y: number } | null {
  return lastPointer.value ?? canvasCenterClientPoint()
}

/** 屏幕坐标 → 画布坐标（走本模块纯函数，不做网格吸附；吸附会让中心偏离鼠标） */
function clientToFlow(client: { x: number; y: number }): { x: number; y: number } | null {
  const rect = canvasRef.value?.querySelector<HTMLElement>(".vue-flow")?.getBoundingClientRect()
  if (!rect) return null
  return clientToFlowPoint(client, { left: rect.left, top: rect.top }, getViewport())
}

/** 新页面节点的落点（节点左上角）：参照点对应的画布坐标 + 重叠错位 */
function pageDropPosition(
  node: WorkflowNode,
  center: { x: number; y: number } | null,
  size: NodeSize,
): [number, number] {
  if (!center) {
    // 既无鼠标位置也无画布尺寸（如未布局的测试环境）：沿用旧的阶梯位置
    return [180 + store.pageNodes.length * 40, 160 + store.pageNodes.length * 20]
  }
  return flowPointToNodePos(center, size)
}

/** 新增页面节点后等它被 VueFlow 量出尺寸（量完 DOM 才有），最长约 320ms */
const NODE_SIZE_POLLS = 20
const NODE_SIZE_POLL_MS = 16

async function waitForNodeSize(nodeId: string): Promise<NodeSize | null> {
  for (let i = 0; i < NODE_SIZE_POLLS; i++) {
    const dims = findFlowNode(nodeId)?.dimensions
    if (dims && dims.width > 0 && dims.height > 0) {
      return { width: dims.width, height: dims.height }
    }
    await new Promise((resolve) => setTimeout(resolve, NODE_SIZE_POLL_MS))
  }
  return null
}

/**
 * 同类节点已被 VueFlow 量出的尺寸（画布单位）。
 * 注册表尺寸（180×82）只是端口布局用的模型，与节点 CSS 实际尺寸（min-width 228 + 动态高度）不同；
 * 能拿到实测值就用实测值，落位一次到位、错位判断也按同一基准比较。画布上还没有同类节点时返回 null。
 */
function measuredSizeFor(type: string): NodeSize | null {
  for (const n of store.nodes) {
    if (n.type !== type) continue
    const dims = findFlowNode(n.id)?.dimensions
    if (dims && dims.width > 0 && dims.height > 0) {
      return { width: dims.width, height: dims.height }
    }
  }
  return null
}

/** 节点的画布尺寸与中心：优先 VueFlow 实测尺寸，取不到就按注册表估算 */
function nodeSize(node: WorkflowNode): NodeSize {
  const dims = findFlowNode(node.id)?.dimensions
  if (dims && dims.width > 0 && dims.height > 0) return { width: dims.width, height: dims.height }
  return { width: node.size[0] || 180, height: store.computeNodeHeight(node) }
}

function nodeCenter(node: WorkflowNode): { x: number; y: number } {
  const size = nodeSize(node)
  return { x: node.pos[0] + size.width / 2, y: node.pos[1] + size.height / 2 }
}

/**
 * 定稿落位：按新节点实测尺寸把中心对到参照点，并按节点中心再查一次重叠错位。
 * 与首帧落位同一套规则，只是尺寸从「估算」换成「实测」，因此不会来回漂。
 */
async function finalizePlacement(nodeId: string, client: { x: number; y: number }): Promise<void> {
  const node = store.findNode(nodeId)
  const center = clientToFlow(client)
  const size = await waitForNodeSize(nodeId)
  if (!node || !center || !size) return
  const target = stackingOffset(center, occupiedCenters(nodeId), PAGE_STACK_STEP)
  node.pos = flowPointToNodePos(target, size)
  refreshFromStore()
}

/** 除自己以外的节点中心（用于重叠错位判断） */
function occupiedCenters(nodeId: string): { x: number; y: number }[] {
  return store.nodes.filter((n) => n.id !== nodeId).map(nodeCenter)
}

function addPage() {
  // 先建节点（数量上限在这里判定），再把它挪到鼠标处：节点高度由 store 按端口数算出，无需猜
  const n = store.createNode("PageNode", 0, 0)
  if (!n) {
    // 达上限：把原因显示到工具栏状态行，与「+ 起点」「+ 终点」同形态（非静默失败）
    status.value = store.statusMessage || "页面节点数量已达上限"
    return
  }
  const client = dropClientPoint()
  const center = client ? clientToFlow(client) : null
  // 首帧：有同类节点的实测尺寸就用它，落位就近；没有就按注册表估算（渲染后定稿会修正）
  const size = measuredSizeFor(n.type) ?? {
    width: n.size[0] || 180,
    height: store.computeNodeHeight(n),
  }
  if (center) {
    const target = stackingOffset(center, occupiedCenters(n.id), PAGE_STACK_STEP)
    n.pos = flowPointToNodePos(target, size)
  } else {
    n.pos = pageDropPosition(n, null, size)
  }
  n.widgets_values = [`页面${store.pageNodes.length}`, "teal"]
  refreshFromStore()
  // 渲染后按新节点自身实测尺寸定稿（尺寸与中心都与首帧同源，避免节点跳位）
  if (client) void finalizePlacement(n.id, client)
}

function addPopup() {
  store.createNode("PopupNode", 420, 320)
  refreshFromStore()
}

function addStart() {
  const n = store.createNode("StartNode", 60, 200)
  if (n) {
    refreshFromStore()
    status.value = "已添加起点（无入口）· 可切换「启动 App / 页面」"
  } else {
    status.value = store.statusMessage || "起点已存在（最多 1 个）"
  }
}

function addEnd() {
  const n = store.createNode("EndNode", 780 + store.endNodes.length * 40, 220)
  if (n) {
    refreshFromStore()
    status.value = "已添加终点（无输出）· 将 navigation 连入其入口"
  } else {
    status.value = store.statusMessage || "终点数量已达上限"
  }
}

function onPaneClick() {
  store.select(null)
}

function onNodeClick({ node }: NodeMouseEvent) {
  store.select(node.id)
}

function onEdgeClick({ edge }: EdgeMouseEvent) {
  const linkId = edge.data?.linkId
  if (linkId != null) store.select("l" + linkId)
}

async function onEdgeDoubleClick({ edge }: EdgeMouseEvent) {
  const linkId = edge.data?.linkId
  if (linkId == null) return
  const link = store.findLink(linkId)
  if (!link) return
  const originNode = store.findNode(link.origin_id)
  const targetNode = store.findNode(link.target_id)
  const fromLabel = originNode?.widgets_values?.[0] || `Node#${link.origin_id}`
  const toLabel = targetNode?.widgets_values?.[0] || `Node#${link.target_id}`
  try {
    await ElMessageBox.confirm(`断开「${fromLabel} → ${toLabel}」的连接？`, "断开连接", {
      confirmButtonText: "断开",
      cancelButtonText: "取消",
      type: "warning",
    })
  } catch {
    // 用户取消断开：ElMessageBox 以 reject 表示取消，不修改画布（非静默吞错）
    return
  }
  store.removeLink(linkId)
  refreshFromStore()
  status.value = `已断开 ${fromLabel} → ${toLabel}`
}

// Keyboard: Delete/Backspace to remove selected link or node
async function onKeyDown(e: KeyboardEvent) {
  if (e.key !== "Delete" && e.key !== "Backspace") return
  // Ignore if you are typing in an input
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return

  const sel = store.selectedId
  if (!sel) return

  if (sel.startsWith("l")) {
    // Selected a link
    const linkId = parseInt(sel.slice(1))
    if (!isNaN(linkId) && store.findLink(linkId)) {
      store.removeLink(linkId)
      refreshFromStore()
      status.value = "已断开连线"
    }
  } else if (sel.startsWith("n")) {
    // Selected a node
    const nodeId = sel.slice(1)
    if (!store.findNode(nodeId)) return
    try {
      await ElMessageBox.confirm(
        `删除节点「${store.findNode(nodeId)?.widgets_values?.[0] || nodeId}」及其所有连线？`,
        "删除确认",
        { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
      )
    } catch {
      // 用户取消删除：ElMessageBox 以 reject 表示取消，不修改画布（非静默吞错）
      return
    }
    store.removeNode(nodeId)
    refreshFromStore()
    status.value = "已删除节点"
  }
}

onMounted(() => window.addEventListener("keydown", onKeyDown))
onUnmounted(() => window.removeEventListener("keydown", onKeyDown))

async function clearAll() {
  try {
    await ElMessageBox.confirm("清空 Vue Flow 画布？", "清空确认", {
      confirmButtonText: "清空",
      cancelButtonText: "取消",
      type: "warning",
    })
  } catch {
    // 用户取消清空：ElMessageBox 以 reject 表示取消，不修改画布（非静默吞错）
    return
  }
  store.clearAll()
  refreshFromStore()
}

function doFit() {
  fitView({ padding: 0.2 })
}

onMounted(async () => {
  if (props.seedDemo) ensureWorkflowSeed(store)
  await refreshFromStore()
  setTimeout(() => fitView({ padding: 0.25 }), 80)
})

watch(
  () => [store.nodes.length, store.links.length, store.bridgedElements.length] as const,
  () => {
    refreshFromStore()
  },
)
</script>

<template>
  <div class="vf-root">
    <div class="vf-toolbar">
      <div class="vf-docbar">
        <button type="button" class="btn back" @click="emit('back')">返回上一级</button>
        <input
          class="doc-name"
          :value="docName"
          placeholder="文件名称…"
          @input="emit('update:docName', ($event.target as HTMLInputElement).value)"
          @change="emit('rename')"
          @blur="emit('rename')"
        />
        <span class="kind-chip">{{ kindLabel }}</span>
        <span v-if="docId" class="id-chip" :title="docId">{{ docId }}</span>
      </div>
      <div class="vf-actions">
        <button class="btn start" @click="addStart" title="最多 1 个 · 无入口">+ 起点</button>
        <button class="btn primary" @click="addPage">+ 页面</button>
        <button class="btn" @click="addPopup">+ 弹窗</button>
        <button class="btn end" @click="addEnd" title="无输出 · 可多终点">+ 终点</button>
        <button class="btn" @click="doFit">适配视图</button>
        <button class="btn" @click="refreshFromStore">刷新</button>
        <button class="btn danger" @click="clearAll">清空</button>
        <span v-if="status" class="hint">{{ status }}</span>
        <span class="meta"
          >节点 {{ store.nodes.length }} · 连线 {{ store.links.length }} · 桥接
          {{ store.bridgedElements.length }}</span
        >
      </div>
    </div>

    <div ref="canvasRef" class="vf-canvas" @mousemove="onCanvasPointerMove">
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :node-types="nodeTypes"
        :connection-mode="connectionMode"
        :is-valid-connection="isValidConnection"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="2.5"
        :snap-to-grid="true"
        :snap-grid="[16, 16]"
        fit-view-on-init
        class="vf-flow"
        @pane-click="onPaneClick"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        @edge-dblclick="onEdgeDoubleClick"
        @node-context-menu="onNodeContextMenu"
      >
        <Background
          pattern-color="#a2d2ff"
          :gap="18"
          :size="1.2"
          bg-color="rgba(255,255,255,0.28)"
        />
        <Controls position="bottom-left" />
        <MiniMap
          position="bottom-right"
          :pannable="true"
          :zoomable="true"
          node-color="#6f9fd8"
          mask-color="rgba(162,210,255,0.22)"
        />
      </VueFlow>
    </div>

    <!-- Element picker（Teleport 到 body，必须用不依赖主题作用域的实色） -->
    <Teleport to="body">
      <div v-if="picker.show" class="el-picker-backdrop" @click="picker.show = false" />
      <div
        v-if="picker.show"
        ref="pickerRef"
        class="el-picker"
        :style="{ left: pickerPosition.x + 'px', top: pickerPosition.y + 'px' }"
        @click.stop
      >
        <div class="el-picker-head">
          <strong>{{ pickerPool[0]?.type === "data" ? "添加响应字段" : "添加元素" }}</strong>
          <span class="el-picker-count"
            >{{ filteredPicker.filter((e) => !e.used).length }} 可选</span
          >
          <button type="button" class="el-picker-close" @click="picker.show = false">×</button>
        </div>
        <input
          v-model="picker.search"
          class="el-picker-search"
          placeholder="搜索元素名称 / 类型…"
          autofocus
        />
        <div class="el-picker-list">
          <button
            v-for="el in filteredPicker"
            :key="el.id"
            type="button"
            class="el-picker-item"
            :class="{ used: el.used }"
            :disabled="el.used"
            @click="!el.used && selectElement(el.id)"
          >
            <span class="el-ico">{{ ELEMENT_ICONS[el.type] || "◆" }}</span>
            <span class="el-body">
              <span class="el-label">{{ el.label }}</span>
              <span class="el-xpath">{{ elXpath(el) }}</span>
            </span>
            <span v-if="el.used" class="el-tag">已添加</span>
            <span v-else class="el-tag add">+ 添加</span>
          </button>
          <div v-if="!filteredPicker.length" class="el-picker-empty">
            {{ pickerPool.length ? "无匹配结果" : "请先右键关联元素管理页面" }}
          </div>
        </div>
      </div>
    </Teleport>

    <NodeContextMenu
      :show="ctxMenu.show"
      :x="ctxMenu.x"
      :y="ctxMenu.y"
      :node-id="ctxMenu.nodeId"
      :node-label="ctxMenu.nodeLabel"
      :can-link-page="ctxMenu.canLinkPage"
      :linked-page-id="ctxMenu.linkedPageId"
      :linked-page-name="ctxMenu.linkedPageName"
      @close="ctxMenu.show = false"
      @link-page="handleLinkPage"
      @resync-page="handleResyncPage"
      @delete-node="handleDeleteFromCtx"
    />

    <EdgeContextMenu
      :show="edgeMenu.show"
      :x="edgeMenu.x"
      :y="edgeMenu.y"
      :link-id="edgeMenu.linkId"
      :label="edgeMenu.label"
      :custom-name="edgeMenu.customName"
      @close="edgeMenu.show = false"
      @rename="handleEdgeRename"
      @delete="handleEdgeDelete"
    />
  </div>
</template>

<style scoped>
.vf-root {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: transparent;
  overflow: hidden;
  /* ── 本模块私有色：tokens.css 未登记，登记在组件根作用域（工具栏消费者均在其内）── */
  --wf-btn-press-shadow: var(--color-ink-05-a05) /* -> --color-ink-05-a05 */; /* 按钮按下硬阴影 */
}
.vf-toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  background: var(--app-bg-card);
  border-bottom: 2px solid var(--ac-border-soft);
  flex-shrink: 0;
}
.vf-docbar {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
  min-width: 0;
}
.vf-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--app-space-sm);
}
.doc-name {
  flex: 1;
  min-width: 140px;
  max-width: 300px;
  padding: 7px 11px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  color: var(--ink);
  outline: none;
  transition: border-color var(--app-duration-fast) var(--app-ease);
}
.doc-name:focus {
  border-color: var(--c-workflow);
}
.kind-chip {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--app-radius-pill);
  background: var(--ac-accent-soft);
  color: var(--ac-accent-deep);
  flex-shrink: 0;
}
.id-chip {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-text-secondary);
  font-family: var(--app-font-mono);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: var(--app-bg-subtle);
  padding: 3px 9px;
  border-radius: var(--app-radius-md);
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 13px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  color: var(--ink);
  font-family: inherit;
  font-size: var(--app-size-sm);
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
  transition:
    background var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease),
    transform 0.12s var(--app-ease);
}
.btn:hover {
  background: var(--ac-accent-soft);
  box-shadow: var(--app-shadow-md);
}
.btn:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 var(--wf-btn-press-shadow);
}
.btn:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 2px;
}
.btn.back {
  flex-shrink: 0;
  color: var(--ac-accent-deep);
}
.btn.primary {
  background: var(--c-workflow);
}
.btn.primary:hover {
  background: var(--c-workflow);
  filter: brightness(1.04);
}
.btn.start {
  color: var(--ac-accent-deep);
}
.btn.end {
  color: var(--app-text-secondary);
}
.btn.danger {
  color: var(--app-status-danger-text);
}
.btn.danger:hover {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}
.hint {
  font-size: var(--app-size-sm);
  color: var(--ac-accent-deep);
  font-weight: 600;
  margin-left: var(--app-space-xs);
  max-width: 40%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  margin-left: auto;
  font-weight: 600;
  white-space: nowrap;
}
.vf-canvas {
  flex: 1;
  min-height: 0;
  background: var(--paper);
}
.vf-flow {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow__controls) {
  box-shadow: var(--app-shadow-md);
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  overflow: hidden;
}
:deep(.vue-flow__controls-button) {
  background: var(--app-bg-card);
  border-bottom: 1px solid var(--ac-border-soft);
  fill: var(--ink);
  width: 28px;
  height: 28px;
}
:deep(.vue-flow__controls-button:hover) {
  background: var(--ac-accent-soft);
}
:deep(.vue-flow__minimap) {
  background: var(--app-bg-card) !important;
  border: 2px solid var(--ink) !important;
  border-radius: var(--app-radius-sm) !important;
}
:deep(.vue-flow__edge-path) {
  stroke-linecap: round;
}
:deep(.vue-flow__attribution) {
  background: transparent !important;
  color: var(--app-text-muted) !important;
}
:deep(.vue-flow__edge-textbg) {
  fill: var(--app-bg-card);
}
:deep(.vue-flow__edge-text) {
  fill: var(--app-text-secondary);
}
</style>

<style>
/* Teleport 到 body：必须实色，不能靠 .workflow-workbench 作用域变量 */
/* ── 选择器私有色：tokens.css 未登记，登记在选择器自身根类（Teleport 到 body 后变量仍可达）── */
.el-picker-backdrop {
  --wf-picker-mask: var(--color-indigo-35-a30) /* -> --color-indigo-35-a30 */; /* 遮罩（墨蓝 26%） */
}
.el-picker {
  --wf-picker-border: var(--color-white-a60) /* -> --color-white-a60 */; /* 亮边（浮层 / 搜索框描边） */
  --wf-picker-shadow: var(--color-indigo-35-a10) /* -> --color-indigo-35-a10 */; /* 浮层投影（墨蓝 12%） */
  --wf-picker-head-border: var(--color-blue-82-a30) /* -> --color-blue-82-a30 */; /* 头部底边分隔 */
  --wf-picker-accent: var(--color-blue-64) /* -> --color-blue-64 */; /* 强调文字（计数 / 可添加标签，工作流深蓝） */
  --wf-picker-count-bg: var(--color-blue-82-a18) /* -> --color-blue-82-a18 */; /* 计数底 */
  --wf-picker-tint-soft: var(--color-blue-82-a18) /* -> --color-blue-82-a18 */; /* 关闭键悬停底 / 标签底 */
  --wf-picker-focus: var(--color-blue-82) /* -> --color-blue-82 */; /* 聚焦描边（浅蓝） */
  --wf-picker-item-border: var(--color-blue-82-a18) /* -> --color-blue-82-a18 */; /* 条目描边 */
  --wf-picker-item-hover-bg: var(--color-blue-82-a10) /* -> --color-blue-82-a10 */; /* 条目悬停底 */
  --wf-picker-used-bg: var(--color-white-a60) /* -> --color-white-a60 */; /* 已使用条目底（灰） */
  --wf-picker-xpath: var(--color-orange-44) /* -> --color-orange-44 */; /* xpath 次要文字（暖灰） */
  --wf-picker-add-bg: var(--color-blue-82-a18) /* -> --color-blue-82-a18 */; /* 可添加标签底 */
}
.el-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal-backdrop);
  background: var(--wf-picker-mask);
}
.el-picker {
  position: fixed;
  z-index: var(--z-modal);
  width: 340px;
  max-height: 420px;
  /* 视口兜底：窗口比浮层还矮时按视口收敛 */
  max-height: min(420px, calc(100vh - 16px));
  max-height: min(420px, calc(100dvh - 16px));
  display: flex;
  flex-direction: column;
  background: var(--app-bg-card);
  border: 1px solid var(--wf-picker-border);
  border-radius: var(--app-radius-lg);
  box-shadow: 4px 4px 0 0 var(--wf-picker-shadow);
  overflow: hidden;
  font-family: var(--app-font, "Cascadia Mono", "Noto Sans SC", sans-serif);
  color: var(--ink);
}
.el-picker-head {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding: 12px 14px;
  background: var(--app-bg-card);
  border-bottom: 1px solid var(--wf-picker-head-border);
}
.el-picker-head strong {
  font-size: var(--app-size-sm);
  font-weight: 800;
}
.el-picker-count {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--wf-picker-accent);
  background: var(--wf-picker-count-bg);
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-pill);
}
.el-picker-close {
  margin-left: auto;
  border: none;
  background: transparent;
  font-size: var(--app-size-lg);
  cursor: pointer;
  color: var(--app-text-secondary);
  line-height: 1;
  padding: 2px 6px;
  border-radius: var(--app-radius-md);
}
.el-picker-close:hover {
  background: var(--wf-picker-tint-soft);
  color: var(--ink);
}
.el-picker-search {
  margin: 10px 12px 6px;
  padding: 9px 12px;
  border: 1.5px solid var(--wf-picker-border);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  font-family: inherit;
  outline: none;
}
.el-picker-search:focus {
  border-color: var(--wf-picker-focus);
}
.el-picker-list {
  /* 高度交给外层 max-height：收敛后条目区自行滚动，条目不会被裁掉 */
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 6px var(--app-space-sm) 12px;
  background: var(--app-bg-card);
}
.el-picker-item {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 10px;
  margin-bottom: var(--app-space-xs);
  border: 1.5px solid var(--wf-picker-item-border);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  color: var(--ink);
}
.el-picker-item:hover:not(:disabled) {
  border-color: var(--wf-picker-focus);
  background: var(--wf-picker-item-hover-bg);
}
.el-picker-item.used {
  opacity: 0.55;
  background: var(--wf-picker-used-bg);
  cursor: not-allowed;
}
.el-ico {
  font-size: var(--app-size-md);
  line-height: 1.2;
  flex-shrink: 0;
}
.el-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.el-label {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
}
.el-xpath {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--wf-picker-xpath);
  word-break: break-all;
  line-height: 1.35;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.el-tag {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 3px var(--app-space-sm);
  border-radius: var(--app-radius-pill);
  background: var(--wf-picker-tint-soft);
  color: var(--app-text-secondary);
  align-self: center;
}
.el-tag.add {
  background: var(--wf-picker-add-bg);
  color: var(--wf-picker-accent);
}
.el-picker-empty {
  padding: var(--app-space-lg) 12px;
  text-align: center;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--app-text-secondary);
}
</style>
