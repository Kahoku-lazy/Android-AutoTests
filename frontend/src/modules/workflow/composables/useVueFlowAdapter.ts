/**
 * Adapt workflowStore ↔ Vue Flow nodes/edges
 */
import type { Node, Edge, Connection } from '@vue-flow/core'
import type { PortDefinition } from '@/modules/workflow/types/workflow'
import { PORT_COLORS, LINK_RULES } from '@/modules/workflow/types/workflow'
import type { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'

type WorkflowStore = ReturnType<typeof useWorkflowStore>

export interface PageFlowNodeData {
  label: string
  nodeType: 'PageNode' | 'PopupNode' | 'StartNode' | 'EndNode'
  color: string
  inputs: PortDefinition[]
  outputs: PortDefinition[]
  canCreateOutput: boolean
  linkedPageId?: string
  linkedPageName?: string
  linkedPageDomain?: string
  isApiNode?: boolean
  apiMethod?: string
  apiUrl?: string
  startKind?: 'app' | 'page' | 'url' | 'api'
  packageName?: string
  startUrl?: string
  startApi?: string
}

export function toVueFlowNodes(store: WorkflowStore): Node<PageFlowNodeData>[] {
  return store.nodes.map(n => ({
    id: n.id,
    type: 'pageFlow',
    position: { x: n.pos[0], y: n.pos[1] },
    data: {
      label: n.widgets_values[0] || n.type,
      nodeType: n.type as PageFlowNodeData['nodeType'],
      color: n.widgets_values[1] || defaultColor(n.type),
      inputs: [...n.inputs],
      outputs: [...n.outputs],
      canCreateOutput: store.canCreateOutput(n),
      linkedPageId: n.properties?.linked_page_id as string | undefined,
      linkedPageName: n.properties?.linked_page_name as string | undefined,
      linkedPageDomain: n.properties?.linked_page_domain as string | undefined,
      startKind: n.type === 'StartNode'
        ? ((n.properties?.start_kind as 'app' | 'page' | 'url' | 'api') || 'app')
        : undefined,
      packageName: n.type === 'StartNode'
        ? ((n.properties?.package_name as string) || 'com.example.app')
        : undefined,
      startUrl: n.type === 'StartNode'
        ? ((n.properties?.start_url as string) || 'https://')
        : undefined,
      startApi: n.type === 'StartNode'
        ? ((n.properties?.start_api as string) || 'http://localhost/api/')
        : undefined,
      isApiNode: n.type === 'ApiNode',
      apiMethod: n.type === 'ApiNode'
        ? ((n.properties?.api_method as string) || 'GET')
        : undefined,
      apiUrl: n.type === 'ApiNode'
        ? ((n.properties?.api_url as string) || '/api/')
        : undefined,
    },
  }))
}

function defaultColor(type: string): string {
  if (type === 'PopupNode') return 'red'
  if (type === 'StartNode') return 'green'
  if (type === 'EndNode') return 'slate'
  return 'teal'
}

export function toVueFlowEdges(store: WorkflowStore): Edge[] {
  return store.links.map(l => {
    const origin = store.findNode(l.origin_id)
    const color = PORT_COLORS[l.type] || '#6a6a78'
    return {
      id: `e-${l.id}`,
      source: l.origin_id,
      target: l.target_id,
      sourceHandle: `out-${l.origin_slot}`,
      targetHandle: `in-${l.target_slot}`,
      type: 'default',
      animated: l.type === 'popup_fixed',
      style: { stroke: color, strokeWidth: 2 },
      label: origin?.outputs[l.origin_slot]?.name || '',
      labelStyle: { fill: '#8a8a96', fontSize: 10 },
      labelBgStyle: { fill: '#1e1e24', fillOpacity: 0.85 },
      data: { linkId: l.id, portType: l.type },
    }
  })
}

/** Normalize: Vue Flow Loose mode may start from target handle → swap to origin→target */
export function normalizeConnection(connection: Connection): Connection {
  const sh = connection.sourceHandle || ''
  const th = connection.targetHandle || ''
  // Drag started on an input handle (in-*) → treat as target side
  if (sh.startsWith('in-') || th.startsWith('out-')) {
    return {
      ...connection,
      source: connection.target,
      target: connection.source,
      sourceHandle: connection.targetHandle,
      targetHandle: connection.sourceHandle,
    }
  }
  return connection
}

export function explainConnection(
  store: WorkflowStore,
  raw: Connection
): { ok: boolean; reason: string; normalized: Connection } {
  const connection = normalizeConnection(raw)
  if (!connection.source || !connection.target) {
    return { ok: false, reason: '缺少源/目标节点', normalized: connection }
  }
  if (connection.source === connection.target) {
    return { ok: false, reason: '不能连接到自身', normalized: connection }
  }

  const sourceNode = store.findNode(connection.source)
  const targetNode = store.findNode(connection.target)
  if (!sourceNode || !targetNode) {
    return { ok: false, reason: '节点不存在', normalized: connection }
  }

  // Cross-domain check: Android pages cannot connect to Web pages
  const srcDomain = sourceNode.properties?.linked_page_domain as string | undefined
  const tgtDomain = targetNode.properties?.linked_page_domain as string | undefined
  if (srcDomain && tgtDomain && srcDomain !== tgtDomain) {
    const srcLabel = srcDomain === 'android' ? 'Android 页面' : 'Web 页面'
    const tgtLabel = tgtDomain === 'android' ? 'Android 页面' : 'Web 页面'
    return {
      ok: false,
      reason: `跨域连线不允许：${srcLabel}不能连接到${tgtLabel}。Android 与 Web 元素管理相互独立，请在各自域内连接。`,
      normalized: connection,
    }
  }

  let outSlot = parseHandleSlot(connection.sourceHandle, 'out')
  let inSlot = parseHandleSlot(connection.targetHandle, 'in')

  // Fallback: single-port side defaults to slot 0 (helps Loose / missing handle id)
  if (outSlot === null && sourceNode.outputs.length === 1) outSlot = 0
  if (inSlot === null && targetNode.inputs.length === 1) inSlot = 0
  if (outSlot === null) {
    return { ok: false, reason: '请从右侧输出端口圆点拖出', normalized: connection }
  }
  if (inSlot === null) {
    return { ok: false, reason: '请拖到目标节点左侧「入口」圆点上', normalized: connection }
  }

  const originPort = sourceNode.outputs[outSlot]
  const targetPort = targetNode.inputs[inSlot]
  if (!originPort || !targetPort) {
    return { ok: false, reason: '端口不存在，请刷新后重试', normalized: connection }
  }

  const allowed = LINK_RULES[originPort.type] || []
  if (!allowed.includes(targetPort.type)) {
    const hint =
      originPort.type === 'popup_fixed'
        ? `「${originPort.name}」当前是 popup_fixed（弹窗触发），只能连弹窗的「触发」口；连页面入口请先把端口类型切回 navigation`
        : `「${originPort.name}」(${originPort.type}) 不能连 「${targetPort.name}」(${targetPort.type})；页面跳转应为 navigation → entry`
    return { ok: false, reason: hint, normalized: connection }
  }

  return {
    ok: true,
    reason: 'ok',
    normalized: {
      ...connection,
      sourceHandle: `out-${outSlot}`,
      targetHandle: `in-${inSlot}`,
    },
  }
}

export function isValidPortConnection(store: WorkflowStore, connection: Connection): boolean {
  return explainConnection(store, connection).status
}

export function applyVueFlowConnect(store: WorkflowStore, connection: Connection): boolean {
  const { ok, normalized, reason } = explainConnection(store, connection)
  if (!ok) {
    store.setStatus(reason)
    return false
  }
  const outSlot = parseHandleSlot(normalized.sourceHandle, 'out')!
  const inSlot = parseHandleSlot(normalized.targetHandle, 'in')!
  const link = store.addLink(normalized.source!, outSlot, normalized.target!, inSlot)
  return !!link
}

function parseHandleSlot(handleId: string | null | undefined, prefix: 'out' | 'in'): number | null {
  if (!handleId || !handleId.startsWith(prefix + '-')) return null
  const n = parseInt(handleId.slice(prefix.length + 1), 10)
  return Number.isFinite(n) ? n : null
}

export function syncNodePositionFromVueFlow(
  store: WorkflowStore,
  nodeId: string,
  position: { x: number; y: number }
): void {
  store.updateNodePosition(nodeId, [Math.round(position.x), Math.round(position.y)])
}

export function portHandleColor(type: string): string {
  return PORT_COLORS[type] || '#5b9cf5'
}

export function ensureWorkflowSeed(store: WorkflowStore): void {
  store.initDemo()
}
