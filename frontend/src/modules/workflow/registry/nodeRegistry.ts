import type { NodeRegistryEntry } from '@/modules/workflow/types/workflow'
import { PORT_TYPE } from '@/modules/workflow/types/workflow'

// ═══════════════════════════════════════════
// NODE REGISTRY — ComfyUI 风格 NODE_CLASS_MAPPINGS
// ═══════════════════════════════════════════

export const NODE_REGISTRY: Record<string, NodeRegistryEntry> = {
  PageNode: {
    category: 'page',
    displayName: '页面节点',
    defaultInputs: [{ name: '入口', type: PORT_TYPE.ENTRY as 'entry' }],
    defaultOutputs: [], // 从元素池动态创建
    color: 'teal',
    icon: '📱',
    maxInstances: 10,
    size: [180, 0],
    elementPool: 'page',
  },
  PopupNode: {
    category: 'popup',
    displayName: '弹窗节点',
    defaultInputs: [{ name: '触发', type: PORT_TYPE.POPUP_TRIGGER as 'popup_trigger' }],
    defaultOutputs: [{ name: '关闭', type: PORT_TYPE.POPUP_CLOSE as 'popup_close' }],
    color: 'red',
    icon: '⚠️',
    maxInstances: Infinity,
    size: [140, 60],
    elementPool: 'popup',
  },
  /** 起点：无入口；默认可输出「启动」；可切为页面起点并挂元素 */
  StartNode: {
    category: 'start',
    displayName: '起点',
    defaultInputs: [],
    defaultOutputs: [{ name: '启动', type: PORT_TYPE.NAVIGATION as 'navigation' }],
    color: 'green',
    icon: '▶',
    maxInstances: 1,
    size: [200, 0],
    elementPool: 'page',
  },
  /** 终点：仅入口、无输出 */
  EndNode: {
    category: 'end',
    displayName: '终点',
    defaultInputs: [{ name: '入口', type: PORT_TYPE.ENTRY as 'entry' }],
    defaultOutputs: [],
    color: 'slate',
    icon: '⏹',
    maxInstances: 5,
    size: [160, 0],
  },
}

// 节点类型对应的颜色样式（用于渲染）
export const COLOR_STYLES: Record<string, { bg: string; border: string; fill: string }> = {
  teal: { bg: 'rgba(25,200,185,0.06)', border: '#19c8b9', fill: '#19c8b9' },
  red: { bg: 'rgba(248,113,113,0.06)', border: '#f87171', fill: '#f87171' },
  blue: { bg: 'rgba(91,156,245,0.06)', border: '#5b9cf5', fill: '#5b9cf5' },
  purple: { bg: 'rgba(167,139,250,0.06)', border: '#a78bfa', fill: '#a78bfa' },
  orange: { bg: 'rgba(245,166,35,0.06)', border: '#f5a623', fill: '#f5a623' },
  green: { bg: 'rgba(111,186,44,0.08)', border: '#6fba2c', fill: '#6fba2c' },
  slate: { bg: 'rgba(138,138,150,0.08)', border: '#8a8a96', fill: '#8a8a96' },
}
