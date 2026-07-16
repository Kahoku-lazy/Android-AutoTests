import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  WorkflowNode,
  Connection,
  PortDefinition,
  WorkflowSaveData,
  BridgedElement,
  StartKind,
  WorkflowCategory,
} from '@/modules/workflow/types/workflow'
import { PORT_TYPE, LINK_RULES, PAGE_ELEMENTS, POPUP_ELEMENTS, findElementDef, MULTI_IN_PORT_TYPES } from '@/modules/workflow/types/workflow'
import { NODE_REGISTRY } from '@/modules/workflow/registry/nodeRegistry'

// ═══════════════════════════════════════════
// PINIA STORE — ComfyUI 工作流状态管理
// ═══════════════════════════════════════════

export const useWorkflowStore = defineStore('wf-workflow', () => {
  // ── State ──
  const nodes = ref<WorkflowNode[]>([])
  const links = ref<Connection[]>([])
  const scale = ref(1)
  const panX = ref(0)
  const panY = ref(0)
  const selectedId = ref<string | null>(null)
  const statusMessage = ref('双击画布或按 N 创建页面节点')
  let nextId = 1

  // ── Getters ──
  const pageNodes = computed(() => nodes.value.filter(n => n.type === 'PageNode'))
  const popupNodes = computed(() => nodes.value.filter(n => n.type === 'PopupNode'))
  const startNodes = computed(() => nodes.value.filter(n => n.type === 'StartNode'))
  const endNodes = computed(() => nodes.value.filter(n => n.type === 'EndNode'))

  /** Elements currently attached as output ports — bridge to test-case editor */
  const bridgedElements = computed((): BridgedElement[] => {
    const result: BridgedElement[] = []
    for (const node of nodes.value) {
      for (const port of node.outputs) {
        if (!port.el) continue
        const def = findElementDef(port.el.id)
        result.push({
          element_id: port.el.id,
          label: port.name,
          type: port.el.type,
          xpath: port.el.xpath || def?.xpath || '',
          page_node_id: node.id,
          page_name: node.widgets_values[0] || node.id,
          port_slot: port.slot_index,
        })
      }
    }
    return result
  })

  function renameNode(id: string, name: string): void {
    const node = findNode(id)
    if (!node || !name.trim()) return
    node.widgets_values[0] = name.trim()
    setStatus('已重命名: ' + name.trim())
  }

  function findNode(id: string): WorkflowNode | undefined {
    return nodes.value.find(n => n.id === id)
  }

  function findLink(id: number): Connection | undefined {
    return links.value.find(l => l.id === id)
  }

  // ── Node Factory ──
  function createNode(type: string, x: number, y: number): WorkflowNode | null {
    const registry = NODE_REGISTRY[type]
    if (!registry) return null

    const existing = nodes.value.filter(n => n.type === type).length
    if (Number.isFinite(registry.maxInstances) && existing >= registry.maxInstances) {
      setStatus(`最多 ${registry.maxInstances} 个「${registry.displayName}」`)
      return null
    }

    const id = 'n' + nextId++
    const properties: Record<string, any> = {}
    if (type === 'StartNode') {
      properties.start_kind = 'app' as StartKind
      properties.package_name = 'com.example.app'
    }

    const node: WorkflowNode = {
      id,
      type,
      pos: [x, y],
      size: [registry.size[0], registry.size[1]],
      category: registry.category as WorkflowCategory,
      inputs: registry.defaultInputs.map((inp, i) => ({
        name: inp.name,
        type: inp.type,
        slot_index: i,
        link: null,
        links: [],
      })),
      outputs: registry.defaultOutputs.map((out, i) => ({
        name: out.name,
        type: out.type,
        slot_index: i,
        link: null,
        links: [],
      })),
      widgets_values: [
        type === 'StartNode' ? '启动 App' : type === 'EndNode' ? '结束' : registry.displayName,
        registry.color,
      ],
      properties,
    }
    nodes.value.push(node)
    setStatus(`已创建: ${registry.displayName}`)
    return node
  }

  /** Switch StartNode between「启动 App」and「页面起点」（始终无入口） */
  function setStartKind(nodeId: string, kind: StartKind): void {
    const node = findNode(nodeId)
    if (!node || node.type !== 'StartNode') return

    // Drop outgoing links before rewriting outputs
    const outIds = links.value.filter(l => l.origin_id === nodeId).map(l => l.id)
    for (const lid of outIds) removeLink(lid)

    node.properties = {
      ...node.properties,
      start_kind: kind,
      package_name: (node.properties?.package_name as string) || 'com.example.app',
    }

    if (kind === 'app') {
      clearElementOutputs(nodeId)
      node.outputs = [{
        name: '启动',
        type: PORT_TYPE.NAVIGATION,
        slot_index: 0,
        link: null,
        links: [],
      }]
      if (!node.widgets_values[0] || node.widgets_values[0] === '起始页面') {
        node.widgets_values[0] = '启动 App'
      }
      setStatus('起点已设为：启动 App（无入口 · 从右侧连出）')
    } else {
      node.outputs = []
      delete node.properties.linked_page_id
      delete node.properties.linked_page_name
      delete node.properties.linked_elements
      if (!node.widgets_values[0] || node.widgets_values[0] === '启动 App') {
        node.widgets_values[0] = '起始页面'
      }
      setStatus('起点已设为：页面（无入口 · 可关联页面/添加元素）')
    }
  }

  function setStartPackage(nodeId: string, pkg: string): void {
    const node = findNode(nodeId)
    if (!node || node.type !== 'StartNode') return
    node.properties = { ...node.properties, package_name: pkg.trim() || 'com.example.app' }
  }

  function removeNode(id: string): void {
    const node = findNode(id)
    if (!node) return
    // Collect link ids attached to this node, then detach port refs on surviving nodes
    const linkIds = links.value
      .filter(l => l.origin_id === id || l.target_id === id)
      .map(l => l.id)
    for (const lid of linkIds) {
      const link = findLink(lid)
      if (!link) continue
      // Clear refs on the *other* side (this node will be deleted)
      if (link.origin_id !== id) {
        const originNode = findNode(link.origin_id)
        const op = originNode?.outputs[link.origin_slot]
        if (op) op.links = op.links.filter(x => x !== lid)
      }
      if (link.target_id !== id) {
        const targetNode = findNode(link.target_id)
        const tp = targetNode?.inputs[link.target_slot]
        if (tp) {
          tp.links = (tp.links || []).filter(x => x !== lid)
          tp.link = tp.links[0] ?? null
        }
      }
    }
    links.value = links.value.filter(l => l.origin_id !== id && l.target_id !== id)
    nodes.value = nodes.value.filter(n => n.id !== id)
    if (selectedId.value === id) selectedId.value = null
    setStatus(`已删除: ${node.widgets_values[0]}`)
  }

  function updateNodePosition(id: string, pos: [number, number]): void {
    const node = findNode(id)
    if (node) node.pos = pos
  }

  // ── Port Management ──
  function addPort(nodeId: string, elId: string, portType?: string): void {
    const node = findNode(nodeId)
    if (!node) return

    const registry = NODE_REGISTRY[node.type]
    const pool = registry?.elementPool === 'popup' ? POPUP_ELEMENTS : PAGE_ELEMENTS
    // Prefer elements from linked page catalog snapshot
    const linkedPool = (node.properties?.linked_elements as typeof PAGE_ELEMENTS | undefined) || []
    const el = linkedPool.find(e => e.id === elId) || pool.find(e => e.id === elId)
    if (!el) return

    addPortFromElement(nodeId, el, portType)
  }

  function addPortFromElement(
    nodeId: string,
    el: { id: string; label: string; type: string; xpath?: string },
    portType?: string
  ): void {
    const node = findNode(nodeId)
    if (!node) return
    if (node.outputs.some(p => p.el?.id === el.id)) return

    const si = node.outputs.length
    node.outputs.push({
      name: el.label,
      type: (portType as any) || PORT_TYPE.NAVIGATION,
      slot_index: si,
      link: null,
      links: [],
      el: { id: el.id, type: el.type, xpath: el.xpath },
    })
    node.size = [180, 0]
  }

  /** Clear all element output ports (and their links) */
  function clearElementOutputs(nodeId: string): void {
    const node = findNode(nodeId)
    if (!node) return
    // Remove links that originate from this node's current outputs
    const outLinkIds = new Set<number>()
    node.outputs.forEach(p => (p.links || []).forEach(id => outLinkIds.add(id)))
    for (const lid of outLinkIds) removeLink(lid)
    node.outputs = []
  }

  /**
   * 关联元素管理页面：只记录页面与元素列表，不自动创建输出端口。
   * 用户通过「添加元素」自行挑选。
   */
  function linkPage(
    nodeId: string,
    page: { id: string; name: string; elements: { id: string; label: string; type: string; xpath?: string }[] }
  ): void {
    const node = findNode(nodeId)
    if (!node) return
    const isPageLike =
      node.type === 'PageNode' ||
      node.type === 'PopupNode' ||
      (node.type === 'StartNode' && node.properties?.start_kind === 'page')
    if (!isPageLike) {
      setStatus('当前节点不能关联页面（起点请先切到「页面」模式）')
      return
    }

    // 换页时清掉旧元素端口（避免残留其它页的输出）
    const prevId = node.properties?.linked_page_id
    if (prevId && String(prevId) !== String(page.id)) {
      clearElementOutputs(nodeId)
    }

    node.properties = {
      ...node.properties,
      linked_page_id: page.id,
      linked_page_name: page.name,
      linked_elements: page.elements,
    }
    node.widgets_values = [page.name, node.widgets_values[1] || 'teal']

    setStatus(
      `已关联「${page.name}」（${page.elements.length} 个可选元素）。请点「+ 添加元素」挑选端口`
    )
  }

  /** 刷新关联页的元素目录；已添加的端口保留，失效元素端口移除 */
  async function resyncLinkedPage(nodeId: string): Promise<boolean> {
    const node = findNode(nodeId)
    if (!node?.properties?.linked_page_id) {
      setStatus('该节点未关联页面')
      return false
    }
    const { fetchCatalogPageById } = await import('@/modules/workflow/data/pageCatalog')
    const page = await fetchCatalogPageById(String(node.properties.linked_page_id))
    if (!page) {
      setStatus('刷新失败：元素管理中找不到该页面')
      return false
    }
    const ids = new Set(page.elements.map(e => e.id))
    // 更新目录
    node.properties = {
      ...node.properties,
      linked_page_id: page.id,
      linked_page_name: page.name,
      linked_elements: page.elements,
    }
    node.widgets_values = [page.name, node.widgets_values[1] || 'teal']
    // 移除已不存在于页面的端口（不自动添加新元素）
    const toRemove = node.outputs
      .filter(p => p.el && !ids.has(p.el.id))
      .map(p => p.slot_index)
      .sort((a, b) => b - a)
    for (const slot of toRemove) removePort(nodeId, slot)

    setStatus(
      `已刷新「${page.name}」元素目录（${page.elements.length} 个可选）；已有端口保留`
    )
    return true
  }

  function removePort(nodeId: string, slotIndex: number): void {
    const node = findNode(nodeId)
    if (!node) return

    // 清理该端口的所有连线
    links.value = links.value.filter(
      l => !(l.origin_id === nodeId && l.origin_slot === slotIndex)
    )
    // 移除端口
    node.outputs = node.outputs.filter(p => p.slot_index !== slotIndex)
    // 重新索引
    node.outputs.forEach((p, i) => (p.slot_index = i))
    // 更新剩余连线的 slot 引用
    links.value.forEach(l => {
      if (l.origin_id === nodeId && l.origin_slot > slotIndex) {
        l.origin_slot--
      }
    })
    if (!node.outputs.length) node.size = [170, 0]
  }

  function togglePortType(nodeId: string, slotIndex: number): void {
    const node = findNode(nodeId)
    if (!node) return
    const port = node.outputs[slotIndex]
    if (!port) return
    port.type = port.type === PORT_TYPE.POPUP_FIXED ? PORT_TYPE.NAVIGATION : PORT_TYPE.POPUP_FIXED
  }

  function addInput(nodeId: string): void {
    const node = findNode(nodeId)
    if (!node) return
    const si = node.inputs.length
    node.inputs.push({
      name: `入口${si + 1}`,
      type: PORT_TYPE.ENTRY as 'entry',
      slot_index: si,
      link: null,
      links: [],
    })
  }

  // ── Link Management ──
  function addLink(
    origin_id: string,
    origin_slot: number,
    target_id: string,
    target_slot: number
  ): Connection | null {
    const originNode = findNode(origin_id)
    const targetNode = findNode(target_id)
    if (!originNode || !targetNode) return null

    const originPort = originNode.outputs[origin_slot]
    const targetPort = targetNode.inputs[target_slot]
    if (!originPort || !targetPort) return null

    // 类型校验
    const allowed = LINK_RULES[originPort.type] || []
    if (!allowed.includes(targetPort.type)) {
      setStatus(
        `连线类型不匹配: ${originPort.name} (${originPort.type}) 不能连接到 ${targetPort.name} (${targetPort.type})`
      )
      return null
    }

    // Ensure arrays exist (loaded legacy data)
    if (!originPort.links) originPort.links = []
    if (!targetPort.links) targetPort.links = []

    // Duplicate same edge → no-op success
    const dup = links.value.find(
      l =>
        l.origin_id === origin_id &&
        l.origin_slot === origin_slot &&
        l.target_id === target_id &&
        l.target_slot === target_slot
    )
    if (dup) {
      setStatus(`连线已存在: ${originPort.name} → ${targetNode.widgets_values[0]}`)
      return dup
    }

    // Single-in ports (e.g. popup_trigger): replace previous inbound
    // Entry (and other MULTI_IN): keep existing connections
    if (!MULTI_IN_PORT_TYPES.has(targetPort.type) && targetPort.links.length > 0) {
      for (const oldId of [...targetPort.links]) removeLink(oldId)
    } else if (!MULTI_IN_PORT_TYPES.has(targetPort.type) && targetPort.link !== null) {
      removeLink(targetPort.link)
    }

    const id = nextId++
    const link: Connection = {
      id,
      origin_id,
      origin_slot,
      target_id,
      target_slot,
      type: originPort.type,
    }
    links.value.push(link)
    originPort.links.push(id)
    targetPort.links.push(id)
    targetPort.link = targetPort.links[0] ?? null
    const inCount = targetPort.links.length
    setStatus(
      MULTI_IN_PORT_TYPES.has(targetPort.type)
        ? `连线成功: ${originPort.name} → ${targetNode.widgets_values[0]}（入口共 ${inCount} 条）`
        : `连线成功: ${originPort.name} → ${targetNode.widgets_values[0]}`
    )
    return link
  }

  function removeLink(id: number): void {
    const link = findLink(id)
    if (!link) return

    const originNode = findNode(link.origin_id)
    const targetNode = findNode(link.target_id)
    if (originNode) {
      const op = originNode.outputs[link.origin_slot]
      if (op) op.links = (op.links || []).filter(lid => lid !== id)
    }
    if (targetNode) {
      const tp = targetNode.inputs[link.target_slot]
      if (tp) {
        tp.links = (tp.links || []).filter(lid => lid !== id)
        tp.link = tp.links[0] ?? null
      }
    }
    links.value = links.value.filter(l => l.id !== id)
    if (selectedId.value === 'l' + id) selectedId.value = null
  }

  // ── Viewport ──
  function updateViewport(newScale: number, newPanX: number, newPanY: number): void {
    scale.value = newScale
    panX.value = newPanX
    panY.value = newPanY
  }

  function resetViewport(): void {
    scale.value = 1
    panX.value = 0
    panY.value = 0
  }

  // ── Selection ──
  function select(id: string | null): void {
    selectedId.value = id
    if (id) {
      const node = findNode(id)
      if (node) setStatus(`选中: ${node.widgets_values[0]}`)
    }
  }

  function setStatus(msg: string): void {
    statusMessage.value = msg
  }

  // ── Persistence ──
  function snapshotGraph(name = 'untitled'): WorkflowSaveData {
    return {
      name,
      version: '1.0',
      savedAt: new Date().toISOString(),
      nodes: JSON.parse(JSON.stringify(nodes.value)),
      links: JSON.parse(JSON.stringify(links.value)),
    }
  }

  function applySnapshot(data: WorkflowSaveData): void {
    nodes.value = data.nodes || []
    links.value = data.links || []
    selectedId.value = null
    normalizePortLinks()
    let max = 0
    nodes.value.forEach(n => {
      const m = parseInt(n.id.slice(1), 10)
      if (!Number.isNaN(m) && m > max) max = m
    })
    links.value.forEach(l => {
      if (l.id > max) max = l.id
    })
    nextId = max + 1
    setStatus('已加载图: ' + (data.name || ''))
  }

  function clearGraph(): void {
    nodes.value = []
    links.value = []
    selectedId.value = null
    nextId = 1
    setStatus('画布已清空')
  }

  function saveToLocal(name: string): void {
    const data = snapshotGraph(name)
    localStorage.setItem('wf_vue_' + name, JSON.stringify(data))
    const idx = JSON.parse(localStorage.getItem('wf_vue_idx') || '[]')
    if (!idx.includes(name)) idx.push(name)
    localStorage.setItem('wf_vue_idx', JSON.stringify(idx))
    setStatus('已保存: ' + name)
  }

  function loadFromLocal(name: string): boolean {
    const raw = localStorage.getItem('wf_vue_' + name)
    if (!raw) return false
    const data: WorkflowSaveData = JSON.parse(raw)
    applySnapshot(data)
    setStatus('已加载: ' + name)
    return true
  }

  /** Migrate legacy single `link` → `links[]` and rebuild from connections table */
  function normalizePortLinks(): void {
    for (const n of nodes.value) {
      for (const p of [...n.inputs, ...n.outputs]) {
        if (!Array.isArray(p.links)) p.links = []
      }
      for (const p of n.inputs) {
        // Rebuild inbound from links table (source of truth)
        p.links = links.value
          .filter(l => l.target_id === n.id && l.target_slot === p.slot_index)
          .map(l => l.id)
        p.link = p.links[0] ?? null
      }
      for (const p of n.outputs) {
        p.links = links.value
          .filter(l => l.origin_id === n.id && l.origin_slot === p.slot_index)
          .map(l => l.id)
        p.link = null
      }
    }
  }

  function getSavedList(): string[] {
    return JSON.parse(localStorage.getItem('wf_vue_idx') || '[]')
  }

  function deleteSaved(name: string): void {
    localStorage.removeItem('wf_vue_' + name)
    const idx = getSavedList().filter(n => n !== name)
    localStorage.setItem('wf_vue_idx', JSON.stringify(idx))
  }

  function exportAPI(): string {
    const api: Record<string, any> = {}
    nodes.value.forEach(n => {
      const inputs: Record<string, any> = {}
      n.inputs.forEach(p => {
        inputs[p.name] = null
      })
      n.outputs.forEach(p => {
        if (p.links && p.links.length) {
          const l = links.value.find(x => x.id === p.links[0])
          if (l) inputs[p.name] = [l.target_id, l.target_slot]
        }
      })
      api[n.id] = { class_type: n.type, inputs }
    })
    return JSON.stringify(api, null, 2)
  }

  function clearAll(): void {
    nodes.value = []
    links.value = []
    selectedId.value = null
    scale.value = 1
    panX.value = 0
    panY.value = 0
    setStatus('画布已清空')
  }

  // ── Business Rules (Component Registry style) ──
  function canCreateOutput(node: WorkflowNode): boolean {
    if (node.type === 'EndNode') return false
    if (node.type === 'StartNode') {
      return node.properties?.start_kind === 'page'
    }
    if (node.type === 'PopupNode') {
      return links.value.some(l => l.target_id === node.id)
    }
    return true // PageNode 始终可以
  }

  function canBeSource(node: WorkflowNode): boolean {
    return node.outputs.length > 0
  }

  // ── Helpers ──
  function screenToCanvas(sx: number, sy: number, svgRect: DOMRect): [number, number] {
    return [(sx - svgRect.left - panX.value) / scale.value, (sy - svgRect.top - panY.value) / scale.value]
  }

  function portPosition(
    node: WorkflowNode,
    port: PortDefinition,
    side: 'left' | 'right'
  ): { x: number; y: number } {
    const ports = side === 'left' ? node.inputs : node.outputs
    const idx = ports.indexOf(port)
    const nodeHeight = computeNodeHeight(node)
    return {
      x: side === 'left' ? node.pos[0] : node.pos[0] + node.size[0],
      y: node.pos[1] + 44 + (idx + 0.5) * 26,
    }
  }

  function computeNodeHeight(node: WorkflowNode): number {
    if (node.size[1] > 0) return node.size[1]
    const rows = Math.max(node.inputs.length, node.outputs.length, 1)
    return 44 + rows * 26 + 12
  }

  // ── Initialize demo data ──
  function initDemo(): void {
    if (nodes.value.length > 0) return // 已有数据不重复初始化

    const start = createNode('StartNode', 40, 200)

    const d1 = createNode('PageNode', 300, 180)
    if (d1) {
      d1.widgets_values = ['首页', 'teal']
      addPort(d1.id, 'el_001', PORT_TYPE.NAVIGATION)
      addPort(d1.id, 'el_003', PORT_TYPE.POPUP_FIXED)
    }

    const d2 = createNode('PageNode', 620, 160)
    if (d2) {
      d2.widgets_values = ['搜索结果页', 'teal']
      addPort(d2.id, 'el_010', PORT_TYPE.NAVIGATION)
      addPort(d2.id, 'el_002', PORT_TYPE.NAVIGATION)
    }

    const d3 = createNode('PopupNode', 640, 380)
    if (d3) d3.widgets_values = ['设置弹窗', 'red']

    const end = createNode('EndNode', 940, 200)

    if (start && d1) addLink(start.id, 0, d1.id, 0)
    if (d1 && d2) addLink(d1.id, 0, d2.id, 0)
    if (d1 && d3) addLink(d1.id, 1, d3.id, 0)
    if (d2 && end) addLink(d2.id, 0, end.id, 0)

    setStatus('起点无入口 · 终点无输出 · 从「启动」连到页面入口')
  }

  return {
    // State
    nodes,
    links,
    scale,
    panX,
    panY,
    selectedId,
    statusMessage,
    // Getters
    pageNodes,
    popupNodes,
    startNodes,
    endNodes,
    bridgedElements,
    findNode,
    findLink,
    // Actions
    createNode,
    removeNode,
    renameNode,
    updateNodePosition,
    setStartKind,
    setStartPackage,
    addPort,
    addPortFromElement,
    clearElementOutputs,
    linkPage,
    resyncLinkedPage,
    removePort,
    togglePortType,
    addInput,
    addLink,
    removeLink,
    updateViewport,
    resetViewport,
    select,
    setStatus,
    saveToLocal,
    loadFromLocal,
    snapshotGraph,
    applySnapshot,
    clearGraph,
    getSavedList,
    deleteSaved,
    exportAPI,
    clearAll,
    canCreateOutput,
    canBeSource,
    screenToCanvas,
    portPosition,
    computeNodeHeight,
    initDemo,
  }
})
