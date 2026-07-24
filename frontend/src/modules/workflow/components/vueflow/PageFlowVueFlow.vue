<script setup lang="ts">
import { ref, computed, watch, provide, onMounted, onUnmounted, markRaw, nextTick } from 'vue'
import { VueFlow, useVueFlow, ConnectionMode } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import type { Connection, NodeMouseEvent, EdgeMouseEvent } from '@vue-flow/core'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import {
  toVueFlowNodes,
  toVueFlowEdges,
  explainConnection,
  applyVueFlowConnect,
  syncNodePositionFromVueFlow,
  ensureWorkflowSeed,
} from '@/modules/workflow/composables/useVueFlowAdapter'
import PageFlowNode from './PageFlowNode.vue'
import NodeContextMenu from './NodeContextMenu.vue'
import { PAGE_ELEMENTS, POPUP_ELEMENTS, ELEMENT_ICONS } from '@/modules/workflow/types/workflow'
import { NODE_REGISTRY } from '@/modules/workflow/registry/nodeRegistry'
import type { CatalogPage, ApiEndpointRef } from '@/modules/workflow/data/pageCatalog'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const emit = defineEmits<{
  addToCase: [payload: { nodeId: string; slotIndex: number; stepType: 'click' | 'wait' }]
  'update:docName': [name: string]
  back: []
  rename: []
}>()

const props = withDefaults(
  defineProps<{
    seedDemo?: boolean
    docName?: string
    docId?: string
  }>(),
  { seedDemo: true, docName: '', docId: '' }
)

const store = useWorkflowStore()
const { onConnect, onNodeDragStop, onEdgesChange, fitView, updateNodeInternals } = useVueFlow()

const nodeTypes = { pageFlow: markRaw(PageFlowNode) }
const connectionMode = ConnectionMode.Loose

const nodes = ref(toVueFlowNodes(store))
const edges = ref(toVueFlowEdges(store))
const status = ref('入口支持多连入：多条 navigation / popup_close 可同时连到同一 entry')

const picker = ref({ show: false, nodeId: '', search: '', x: 200, y: 120 })

const ctxMenu = ref({
  show: false,
  x: 0,
  y: 0,
  nodeId: '',
  nodeLabel: '',
  canLinkPage: true,
  linkedPageId: undefined as string | undefined,
  linkedPageName: undefined as string | undefined,
})

function openNodeContext(e: MouseEvent | TouchEvent, nodeId: string) {
  e.preventDefault()
  const node = store.findNode(nodeId)
  if (!node) return
  store.select(nodeId)
  const clientX = 'clientX' in e ? e.clientX : (e.touches?.[0]?.clientX ?? 0)
  const clientY = 'clientY' in e ? e.clientY : (e.touches?.[0]?.clientY ?? 0)
  const canLink =
    node.type === 'PageNode' ||
    node.type === 'PopupNode' ||
    (node.type === 'StartNode' && node.properties?.start_kind !== 'app')
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

function handleLinkApi(endpoint: ApiEndpointRef) {
  if (!ctxMenu.value.nodeId) return
  store.linkApiEndpoint(ctxMenu.value.nodeId, endpoint)
  refreshFromStore()
  status.value = store.statusMessage || `已关联 API「${endpoint.name}」`
}

async function handleResyncPage() {
  if (!ctxMenu.value.nodeId) return
  const ok = await store.resyncLinkedPage(ctxMenu.value.nodeId)
  refreshFromStore()
  status.value = store.statusMessage || (ok ? '元素已刷新' : '刷新失败')
}

function handleDeleteFromCtx() {
  if (!ctxMenu.value.nodeId) return
  store.removeNode(ctxMenu.value.nodeId)
  refreshFromStore()
  status.value = '节点已删除'
}

async function refreshFromStore() {
  nodes.value = toVueFlowNodes(store)
  edges.value = toVueFlowEdges(store)
  await nextTick()
  const ids = store.nodes.map(n => n.id)
  if (ids.length) updateNodeInternals(ids)
}

provide('vfOpenPicker', (nodeId: string) => {
  picker.value = { show: true, nodeId, search: '', x: 280, y: 140 }
})

provide('vfRefresh', () => {
  refreshFromStore()
})

provide('vfAddToCase', (nodeId: string, slot: number, step: 'click' | 'wait') => {
  emit('addToCase', { nodeId, slotIndex: slot, stepType: step })
})

const pickerPool = computed(() => {
  const node = store.findNode(picker.value.nodeId)
  if (!node) return PAGE_ELEMENTS
  const linked = node.properties?.linked_elements as typeof PAGE_ELEMENTS | undefined
  if (linked?.length) return linked
  return NODE_REGISTRY[node.type]?.elementPool === 'popup' ? POPUP_ELEMENTS : PAGE_ELEMENTS
})

const filteredPicker = computed(() => {
  const q = picker.value.search.toLowerCase()
  const node = store.findNode(picker.value.nodeId)
  const used = new Set(node?.outputs.map(p => p.el?.id).filter(Boolean))
  return pickerPool.value
    .filter(e => !q || e.label.toLowerCase().includes(q) || e.type.includes(q))
    .map(e => ({ ...e, used: used.has(e.id) }))
})

function selectElement(elId: string) {
  const item = filteredPicker.value.find(x => x.id === elId)
  if (!item || item.used) return
  store.addPort(picker.value.nodeId, elId)
  picker.value.show = false
  refreshFromStore()
  status.value = '已添加元素: ' + item.label
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
    status.value = '连线成功 ✓ navigation → entry'
  } else {
    status.value = store.statusMessage || '连线失败'
  }
})

onNodeDragStop(({ node }) => {
  syncNodePositionFromVueFlow(store, node.id, node.position)
})

onEdgesChange((changes) => {
  for (const ch of changes) {
    if (ch.type === 'remove') {
      const edge = edges.value.find(e => e.id === ch.id)
      const linkId = edge?.data?.linkId as number | undefined
      if (linkId != null) store.removeLink(linkId)
    }
  }
  setTimeout(() => refreshFromStore(), 0)
})

function addPage() {
  const n = store.createNode('PageNode', 180 + store.pageNodes.length * 40, 160 + store.pageNodes.length * 20)
  if (n) {
    n.widgets_values = [`页面${store.pageNodes.length}`, 'teal']
    refreshFromStore()
  }
}

function addPopup() {
  store.createNode('PopupNode', 420, 320)
  refreshFromStore()
}

function addApi() {
  const count = store.nodes.filter(n => n.type === 'ApiNode').length
  const n = store.createNode('ApiNode', 300, 80 + count * 60)
  if (n) {
    n.widgets_values = [`API 接口${count + 1}`, 'orange']
    refreshFromStore()
  }
}

function addStart() {
  const n = store.createNode('StartNode', 60, 200)
  if (n) {
    refreshFromStore()
    status.value = '已添加起点（无入口）· 可切换「启动 App / 页面」'
  } else {
    status.value = store.statusMessage || '起点已存在（最多 1 个）'
  }
}

function addEnd() {
  const n = store.createNode('EndNode', 780 + store.endNodes.length * 40, 220)
  if (n) {
    refreshFromStore()
    status.value = '已添加终点（无输出）· 将 navigation 连入其入口'
  } else {
    status.value = store.statusMessage || '终点数量已达上限'
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
  if (linkId != null) store.select('l' + linkId)
}

// Double-click edge to delete with confirmation
function onEdgeDoubleClick({ edge }: EdgeMouseEvent) {
  const linkId = edge.data?.linkId
  if (linkId == null) return
  const link = store.findLink(linkId)
  if (!link) return
  const originNode = store.findNode(link.origin_id)
  const targetNode = store.findNode(link.target_id)
  const fromLabel = originNode?.widgets_values?.[0] || `Node#${link.origin_id}`
  const toLabel = targetNode?.widgets_values?.[0] || `Node#${link.target_id}`
  if (confirm(`断开「${fromLabel} → ${toLabel}」的连接？`)) {
    store.removeLink(linkId)
    refreshFromStore()
    status.value = `已断开 ${fromLabel} → ${toLabel}`
  }
}

// Keyboard: Delete/Backspace to remove selected link or node
function onKeyDown(e: KeyboardEvent) {
  if (e.key !== 'Delete' && e.key !== 'Backspace') return
  // Ignore if user is typing in an input
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  const sel = store.selectedId.value
  if (!sel) return

  if (sel.startsWith('l')) {
    // Selected a link
    const linkId = parseInt(sel.slice(1))
    if (!isNaN(linkId) && store.findLink(linkId)) {
      store.removeLink(linkId)
      refreshFromStore()
      status.value = '已断开连线'
    }
  } else if (sel.startsWith('n')) {
    // Selected a node
    const nodeId = sel.slice(1)
    if (store.findNode(nodeId)) {
      if (confirm(`删除节点「${store.findNode(nodeId)?.widgets_values?.[0] || nodeId}」及其所有连线？`)) {
        store.removeNode(nodeId)
        refreshFromStore()
        status.value = '已删除节点'
      }
    }
  }
}

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

function clearAll() {
  if (!confirm('清空 Vue Flow 画布？')) return
  store.clearAll()
  refreshFromStore()
}

function doFit() {
  fitView({ padding: 0.2 })
}

function rewireSearchDemo() {
  // Ensure 搜索图标 (slot0 on 首页) → 搜索结果页 entry
  const home = store.pageNodes.find(n => n.widgets_values[0] === '首页') || store.pageNodes[0]
  const results = store.pageNodes.find(n => n.widgets_values[0] === '搜索结果页') || store.pageNodes[1]
  if (!home || !results) {
    status.value = '缺少首页或搜索结果页，请先创建节点'
    return
  }
  const searchSlot = home.outputs.findIndex(p => p.el?.id === 'el_001' || p.name.includes('搜索'))
  if (searchSlot < 0) {
    store.addPort(home.id, 'el_001')
  }
  const slot = home.outputs.findIndex(p => p.el?.id === 'el_001' || p.name.includes('搜索'))
  if (slot >= 0 && home.outputs[slot].type !== 'navigation') {
    home.outputs[slot].type = 'navigation' as any
  }
  const ok = store.addLink(home.id, slot >= 0 ? slot : 0, results.id, 0)
  refreshFromStore()
  status.value = ok
    ? '已自动连接：搜索图标 → 搜索结果页入口'
    : store.statusMessage
}

onMounted(async () => {
  if (props.seedDemo) ensureWorkflowSeed(store)
  await refreshFromStore()
  setTimeout(() => fitView({ padding: 0.25 }), 80)
})

watch(
  () => [store.nodes.length, store.links.length, store.bridgedElements.length] as const,
  () => { refreshFromStore() }
)

</script>

<template>
  <div class="vf-root">
    <div class="vf-toolbar">
      <div class="vf-docbar">
        <button type="button" class="btn back" @click="emit('back')">← 看板</button>
        <input
          class="doc-name"
          :value="docName"
          placeholder="文件名称…"
          @input="emit('update:docName', ($event.target as HTMLInputElement).value)"
          @change="emit('rename')"
          @blur="emit('rename')"
        />
        <span class="kind-chip">页面流</span>
        <span v-if="docId" class="id-chip" :title="docId">{{ docId }}</span>
      </div>
      <div class="vf-actions">
        <button class="btn start" @click="addStart" title="最多 1 个 · 无入口">+ 起点</button>
        <button class="btn primary" @click="addPage">+ 页面</button>
        <button class="btn" @click="addPopup">+ 弹窗</button>
        <button class="btn end" @click="addEnd" title="无输出 · 可多终点">+ 终点</button>
        <button class="btn api-btn" @click="addApi" title="数据流节点 · 关联接口后生成端口">+ API</button>
        <button class="btn" @click="rewireSearchDemo" title="强制连接 搜索图标→搜索结果页入口">连搜索示例</button>
        <button class="btn" @click="doFit">适配视图</button>
        <button class="btn" @click="refreshFromStore">刷新</button>
        <button class="btn danger" @click="clearAll">清空</button>
        <span class="hint">{{ status }}</span>
        <span class="meta">节点 {{ store.nodes.length }} · 连线 {{ store.links.length }} · 桥接 {{ store.bridgedElements.length }}</span>
      </div>
    </div>

    <div class="vf-canvas">
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
        <Background pattern-color="#a2d2ff" :gap="18" :size="1.2" bg-color="rgba(255,255,255,0.28)" />
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
        class="el-picker"
        :style="{ left: picker.x + 'px', top: picker.y + 'px' }"
        @click.stop
      >
        <div class="el-picker-head">
          <strong>添加元素</strong>
          <span class="el-picker-count">{{ filteredPicker.filter(e => !e.used).length }} 可选</span>
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
            <span class="el-ico">{{ ELEMENT_ICONS[el.type] || '◆' }}</span>
            <span class="el-body">
              <span class="el-label">{{ el.label }}</span>
              <span class="el-xpath">{{ el.xpath || el.type }}</span>
            </span>
            <span v-if="el.used" class="el-tag">已添加</span>
            <span v-else class="el-tag add">+ 添加</span>
          </button>
          <div v-if="!filteredPicker.length" class="el-picker-empty">
            {{ pickerPool.length ? '无匹配结果' : '请先右键关联元素管理页面' }}
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
      :node-type="store.findNode(ctxMenu.nodeId)?.type"
      :can-link-page="ctxMenu.canLinkPage"
      :linked-page-id="ctxMenu.linkedPageId"
      :linked-page-name="ctxMenu.linkedPageName"
      @close="ctxMenu.show = false"
      @link-page="handleLinkPage"
      @link-api="handleLinkApi"
      @resync-page="handleResyncPage"
      @delete-node="handleDeleteFromCtx"
    />
  </div>
</template>

<style scoped>
.vf-root {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--ac-paper);
  border: 2px solid var(--ac-border);
  border-radius: var(--ac-radius);
  box-shadow: var(--ac-shadow);
  overflow: hidden;
}
.vf-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.46);
  border-bottom: 1px solid var(--ink);
  flex-shrink: 0;
}
.vf-docbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}
.vf-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.doc-name {
  flex: 1;
  min-width: 120px;
  max-width: 260px;
  padding: 6px 10px;
  border: 2px solid var(--ac-border);
  border-radius: 10px;
  background: #fff;
  font-size: var(--app-size-sm);
  font-weight: 800;
  font-family: inherit;
  color: var(--ac-ink);
  outline: none;
}
.doc-name:focus { border-color: var(--app-blue); }
.kind-chip {
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(162,210,255,0.16);
  color: var(--app-green-deep);
  flex-shrink: 0;
}
.id-chip {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-green-deep);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(162,210,255,0.12);
  padding: 3px 8px;
  border-radius: 8px;
}
.btn.back {
  flex-shrink: 0;
  background: #fff;
  color: var(--app-green-deep);
  border-color: rgba(162,210,255,0.42);
}
.btn {
  padding: 7px 12px;
  border: 2px solid var(--ac-border);
  border-radius: 999px;
  background: var(--ac-paper);
  color: var(--ac-ink-muted);
  font-family: inherit;
  font-size: var(--app-size-sm);
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
  transition: all 0.15s ease;
}
.btn:hover {
  border-color: var(--ac-teal);
  color: var(--app-green-deep);
  transform: translateY(-1px);
}
.btn.primary {
  background: linear-gradient(135deg, var(--app-green-deep), var(--app-blue));
  color: #fff;
  border-color: var(--app-green-deep);
}
.btn.primary:hover { filter: brightness(1.05); color: #fff; }
.btn.start {
  background: var(--c-workflow);
  color: #fff;
  border-color: #5a9a20;
}
.btn.start:hover { filter: brightness(1.05); color: #fff; }
.btn.end {
  background: #8a8a96;
  color: #fff;
  border-color: #6a6a76;
}
.btn.end:hover { filter: brightness(1.05); color: #fff; }
.btn.api-btn { background: rgba(245, 166, 35, 0.12); color: #d4880f; border-color: rgba(245, 166, 35, 0.3); }
.btn.api-btn:hover { filter: brightness(1.05); color: #fff; background: #f5a623; }
.btn.danger:hover {
  border-color: var(--ac-red);
  color: var(--ac-red);
}
.hint {
  font-size: var(--app-size-sm);
  color: var(--app-green-deep);
  font-weight: 600;
  margin-left: 4px;
}
.meta {
  font-size: var(--app-size-xs);
  color: var(--ac-ink-faint);
  margin-left: auto;
  font-weight: 600;
}
.vf-canvas { flex: 1; min-height: 0; background: var(--ac-cream); }
.vf-flow { width: 100%; height: 100%; }

:deep(.vue-flow__controls) {
  box-shadow: var(--ac-shadow);
  border: 2px solid var(--ac-border);
  border-radius: 12px;
  overflow: hidden;
}
:deep(.vue-flow__controls-button) {
  background: var(--ac-paper);
  border-bottom: 1px solid var(--ac-border-soft);
  fill: var(--ac-wood);
  width: 28px;
  height: 28px;
}
:deep(.vue-flow__controls-button:hover) {
  background: var(--ac-cream-deep);
}
:deep(.vue-flow__minimap) {
  background: var(--ac-paper) !important;
  border: 2px solid var(--ac-border) !important;
  border-radius: 12px !important;
}
:deep(.vue-flow__edge-path) {
  stroke-linecap: round;
}
:deep(.vue-flow__attribution) {
  background: transparent !important;
  color: var(--ac-ink-faint) !important;
}
:deep(.vue-flow__edge-textbg) {
  fill: var(--ac-paper);
}
:deep(.vue-flow__edge-text) {
  fill: var(--ac-ink-muted);
}
</style>

<style>
/* Teleport 到 body：必须实色，不能靠 .workflow-workbench 作用域变量 */
.el-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9990;
  background: rgba(74,78,105,0.26);
}
.el-picker {
  position: fixed;
  z-index: 9991;
  width: 340px;
  max-height: 420px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid rgba(255,255,255,0.68);
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(74,78,105,0.12);
  overflow: hidden;
  font-family: var(--app-font, 'Nunito', 'PingFang SC', sans-serif);
  color: var(--ink);
  
}
.el-picker-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #fff;
  border-bottom: 1px solid rgba(162,210,255,0.24);
}
.el-picker-head strong {
  font-size: var(--app-size-sm);
  font-weight: 800;
}
.el-picker-count {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: #6f9fd8;
  background: rgba(162,210,255,0.16);
  padding: 2px 8px;
  border-radius: 999px;
}
.el-picker-close {
  margin-left: auto;
  border: none;
  background: transparent;
  font-size: var(--app-size-lg);
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 8px;
}
.el-picker-close:hover { background: rgba(162,210,255,0.14); color: var(--ink); }
.el-picker-search {
  margin: 10px 12px 6px;
  padding: 9px 12px;
  border: 1.5px solid rgba(255,255,255,0.68);
  border-radius: 10px;
  background: #ffffff;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  font-family: inherit;
  outline: none;
}
.el-picker-search:focus { border-color: #a2d2ff; }
.el-picker-list {
  flex: 1;
  overflow: auto;
  padding: 6px 8px 12px;
  max-height: 300px;
  background: #fff;
}
.el-picker-item {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 10px;
  margin-bottom: 4px;
  border: 1.5px solid rgba(162,210,255,0.22);
  border-radius: 12px;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  color: var(--ink);
}
.el-picker-item:hover:not(:disabled) {
  border-color: #a2d2ff;
  background: rgba(162,210,255,0.12);
}
.el-picker-item.used {
  opacity: 0.55;
  background: rgba(235,237,238,0.58);
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
  color: #7a6b5a;
  word-break: break-all;
  line-height: 1.35;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.el-tag {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(162,210,255,0.14);
  color: #999;
  align-self: center;
}
.el-tag.add {
  background: rgba(162,210,255,0.18);
  color: #6f9fd8;
}
.el-picker-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: #999;
}
</style>
