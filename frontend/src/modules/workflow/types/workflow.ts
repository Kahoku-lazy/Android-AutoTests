// ═══════════════════════════════════════════
// PORT TYPE SYSTEM — ComfyUI 风格强类型端口
// ═══════════════════════════════════════════

export const PORT_TYPE = {
  ENTRY: 'entry',
  POPUP_TRIGGER: 'popup_trigger',
  NAVIGATION: 'navigation',
  POPUP_FIXED: 'popup_fixed',
  POPUP_CLOSE: 'popup_close',
  DATA: 'data',
} as const

export type PortType = (typeof PORT_TYPE)[keyof typeof PORT_TYPE]

// 连线类型校验规则表
export const LINK_RULES: Record<string, string[]> = {
  navigation: ['entry'],
  popup_fixed: ['popup_trigger'],
  popup_close: ['entry'],
  data: ['data'],
}

// 端口类型 → 显示颜色
export const PORT_COLORS: Record<string, string> = {
  entry: '#5b9cf5',
  popup_trigger: '#f87171',
  navigation: '#a78bfa',
  popup_fixed: '#f87171',
  popup_close: '#8a8a96',
}

// ═══════════════════════════════════════════
// CORE DATA TYPES
// ═══════════════════════════════════════════

export interface PortDefinition {
  name: string
  type: PortType
  slot_index: number
  /** @deprecated Prefer links[]; kept as links[0] ?? null for legacy reads */
  link: number | null
  /** Incoming (input) or outgoing (output) link IDs. Entry inputs support multiple. */
  links: number[]
  el?: { id: string; type: string; xpath?: string }
}

/** Ports that accept multiple inbound connections */
export const MULTI_IN_PORT_TYPES: ReadonlySet<string> = new Set([PORT_TYPE.ENTRY])


export type WorkflowNodeType = 'PageNode' | 'PopupNode' | 'StartNode' | 'EndNode' | 'ApiNode'
export type WorkflowCategory = 'page' | 'popup' | 'start' | 'end'
/** StartNode: launch app / open URL / call API / page-as-entry */
export type StartKind = 'app' | 'page' | 'url' | 'api'

export interface WorkflowNode {
  id: string
  type: WorkflowNodeType | string
  pos: [number, number] // [x, y]
  size: [number, number] // [w, h], h=0 自动计算
  category: WorkflowCategory
  inputs: PortDefinition[]
  outputs: PortDefinition[]
  widgets_values: [string, string] // [名称, 颜色]
  properties: Record<string, any>
}

export interface Connection {
  id: number
  origin_id: string
  origin_slot: number
  target_id: string
  target_slot: number
  type: PortType
}

export interface NodeRegistryEntry {
  category: string
  displayName: string
  defaultInputs: { name: string; type: PortType }[]
  defaultOutputs: { name: string; type: PortType }[]
  color: string
  icon: string
  maxInstances: number
  size: [number, number]
  elementPool?: 'page' | 'popup'
}

// ═══════════════════════════════════════════
// ELEMENT POOLS — with xpath for automation bridge
// ═══════════════════════════════════════════

export interface ElementDef {
  id: string
  label: string
  type: string
  /** Optional XPath locator for automation / test-case bridge */
  xpath?: string
}

export const PAGE_ELEMENTS: ElementDef[] = [
  { id: 'el_001', label: '搜索图标', type: 'icon', xpath: '//*[@resource-id="com.taobao.taobao:id/search_btn"]' },
  { id: 'el_002', label: '我的按钮', type: 'button', xpath: '//*[@text="我的"]' },
  { id: 'el_003', label: '设置按钮', type: 'button', xpath: '//*[@resource-id="com.taobao.taobao:id/settings"]' },
  { id: 'el_004', label: '购物车图标', type: 'icon', xpath: '//*[@resource-id="com.taobao.taobao:id/cart"]' },
  { id: 'el_005', label: '返回按钮', type: 'button', xpath: '//*[@content-desc="返回"]' },
  { id: 'el_006', label: '首页Banner', type: 'image', xpath: '//*[@resource-id="com.taobao.taobao:id/banner"]' },
  { id: 'el_007', label: '推荐位1', type: 'link', xpath: '//*[@resource-id="recommend"][1]' },
  { id: 'el_008', label: '推荐位2', type: 'link', xpath: '//*[@resource-id="recommend"][2]' },
  { id: 'el_009', label: '分类Tab', type: 'tab', xpath: '//*[@text="分类"]' },
  { id: 'el_010', label: '商品卡片', type: 'card', xpath: '//*[@resource-id="result_item"]' },
  { id: 'el_011', label: '底部导航-首页', type: 'nav', xpath: '//*[@text="首页"]' },
  { id: 'el_012', label: '底部导航-我的', type: 'nav', xpath: '//android.widget.TextView[@text="我的"]' },
  { id: 'el_013', label: '确认按钮', type: 'button', xpath: '//*[@text="确认"]' },
  { id: 'el_014', label: '分享按钮', type: 'button', xpath: '//*[@content-desc="分享"]' },
]

export const POPUP_ELEMENTS: ElementDef[] = [
  { id: 'pe_001', label: '关闭按钮', type: 'button', xpath: '//*[@resource-id="dialog_close"]' },
  { id: 'pe_002', label: '确认按钮', type: 'button', xpath: '//*[@text="确认"]' },
  { id: 'pe_003', label: '取消按钮', type: 'button', xpath: '//*[@text="取消"]' },
  { id: 'pe_004', label: '弹窗标题', type: 'text', xpath: '//*[@resource-id="dialog_title"]' },
  { id: 'pe_005', label: '弹窗描述', type: 'text', xpath: '//*[@resource-id="dialog_msg"]' },
  { id: 'pe_006', label: '我知道了按钮', type: 'button', xpath: '//*[@text="我知道了"]' },
  { id: 'pe_007', label: '不再提示', type: 'checkbox', xpath: '//*[@text="不再提示"]' },
  { id: 'pe_008', label: '前往设置', type: 'link', xpath: '//*[@text="前往设置"]' },
]

export const ELEMENT_ICONS: Record<string, string> = {
  icon: '◆',
  button: '●',
  image: '▣',
  link: '→',
  tab: '≡',
  card: '▨',
  nav: '■',
  text: '¶',
  checkbox: '☑',
}

/** Look up element definition by id across both pools */
export function findElementDef(elId: string): ElementDef | undefined {
  return PAGE_ELEMENTS.find(e => e.id === elId) || POPUP_ELEMENTS.find(e => e.id === elId)
}

// ═══════════════════════════════════════════
// CONTEXT MENU
// ═══════════════════════════════════════════

export interface ContextMenuItem {
  icon?: string
  label: string
  action: string
  danger?: boolean
  disabled?: boolean
  shortcut?: string
}

// ═══════════════════════════════════════════
// SAVE / LOAD
// ═══════════════════════════════════════════

export interface WorkflowSaveData {
  name: string
  version: string
  savedAt: string
  nodes: WorkflowNode[]
  links: Connection[]
}

/** Bridge item: an element attached as a page-flow output port */
export interface BridgedElement {
  element_id: string
  label: string
  type: string
  xpath: string
  page_node_id: string
  page_name: string
  port_slot: number
}
