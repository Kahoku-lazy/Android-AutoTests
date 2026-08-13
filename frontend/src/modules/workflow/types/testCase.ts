// ═══════════════════════════════════════════
// TEST CASE TYPES — Scratch 风格树形 Block 模型
// ═══════════════════════════════════════════

// ── 16 Step Types (aligned with models/step_types.py StepType enum) ──
export const STEP_TYPE_META: Record<string, { icon: string; label: string; color: string; category: string; notchColor: string }> = {
  // 点击操作
  click:          { icon: '👆', label: '点击元素',     color: '#5b9cf5', category: '点击操作', notchColor: '#4a8adf' },
  long_click:     { icon: '👇', label: '长按元素',     color: '#5b9cf5', category: '点击操作', notchColor: '#4a8adf' },
  // 滑动操作
  swipe:          { icon: '👈', label: '滑动屏幕',     color: '#a78bfa', category: '滑动操作', notchColor: '#8b6ee0' },
  // 等待操作
  wait:           { icon: '⏳', label: '等待出现',     color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  wait_disappear: { icon: '👻', label: '等待消失',     color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  sleep:          { icon: '💤', label: '固定等待',     color: '#8a8a96', category: '等待操作', notchColor: '#6a6a76' },
  // 断言操作
  verify_text:    { icon: '✓', label: '验证文本',     color: '#6fba2c', category: '断言操作', notchColor: '#5a9a20' },
  poll_text:      { icon: '🔍', label: '轮询文本',     color: '#6fba2c', category: '断言操作', notchColor: '#5a9a20' },
  // 应用控制
  start_app:      { icon: '📱', label: '启动App',      color: '#19c8b9', category: '应用控制', notchColor: '#14a398' },
  kill_app:       { icon: '💀', label: '杀掉App',      color: '#f87171', category: '应用控制', notchColor: '#e55a5a' },
  // APP性能
  perf_element_time: { icon: '⏱️', label: '等待元素出现耗时', color: '#f5a623', category: 'APP性能', notchColor: '#e09515' },
  // 弹窗检测
  wait_toast:     { icon: '💬', label: '等待Toast',    color: '#f5a623', category: '弹窗检测', notchColor: '#e09515' },
  // 流程控制
  if_element_appear:    { icon: '🔀', label: '如果元素出现',   color: '#f5a623', category: '流程控制', notchColor: '#e09515' },
  if_element_disappear: { icon: '🔀', label: '如果元素消失',   color: '#f5a623', category: '流程控制', notchColor: '#e09515' },
  loop_n:               { icon: '🔁', label: '循环N次',        color: '#a78bfa', category: '流程控制', notchColor: '#8b6ee0' },
  loop_elements:        { icon: '📋', label: '遍历元素列表',   color: '#a78bfa', category: '流程控制', notchColor: '#8b6ee0' },
}

export type StepTypeValue = keyof typeof STEP_TYPE_META

/** Steps that typically need an element locator (xpath) */
export const STEPS_NEED_XPATH = new Set([
  'click', 'long_click',
  'wait', 'wait_disappear',
  'verify_text', 'poll_text',
  'perf_element_time',
  'if_element_appear', 'if_element_disappear',
  'loop_elements',
])

/** Steps that need package_name (use xpath field as package name) */
export const STEPS_NEED_PACKAGE = new Set(['start_app', 'kill_app'])

/** Steps that show timeout field */
export const STEPS_NEED_TIMEOUT = new Set([
  'click', 'long_click',
  'wait', 'wait_disappear',
  'verify_text', 'poll_text', 'sleep',
  'perf_element_time', 'wait_toast',
  'if_element_appear', 'if_element_disappear',
])

// ── Flow Control Meta ──
export const FLOW_META = {
  branch: { icon: '◈', label: '条件分支', color: '#f5a623', notchColor: '#e09515' },
  loop:   { icon: '↻', label: '循环',     color: '#a78bfa', notchColor: '#8b6ee0' },
} as const

// ── Block Status ──
export type StepStatus = 'pending' | 'running' | 'pass' | 'fail'

// ═══════════════════════════════════════════
// TREE-STRUCTURED BLOCK TYPES
// ═══════════════════════════════════════════

export interface StepBlock {
  package_name?: string
  id: string
  kind: 'step'
  stepType: StepTypeValue
  /** Display label on the block (synced with description) */
  label: string
  /** Platform TestStep.description */
  description: string
  xpath: string
  xpath2: string
  timeout: number
  expected_text: string
  index: number
  direction: string
  distance: number
  /** Optional bridge: element from page-flow */
  element_id?: string
  element_label?: string
  status: StepStatus
}

export interface BranchBlock {
  id: string
  kind: 'branch'
  condition: string
  passChildren: Block[]
  failChildren: Block[]
  collapsed: boolean
}

export interface LoopBlock {
  id: string
  kind: 'loop'
  count: number
  description: string
  children: Block[]
  collapsed: boolean
}

export type Block = StepBlock | BranchBlock | LoopBlock

// ── Platform-aligned flat step (case-manager compatible) ──
export interface FlatTestStep {
  package_name?: string
  type: string
  xpath: string
  xpath2: string
  timeout: number
  expected_text: string
  index: number
  direction: string
  distance: number
  description: string
}

// ── Block helpers ──
export function isContainer(b: Block): b is BranchBlock | LoopBlock {
  return b.kind === 'branch' || b.kind === 'loop'
}

export function blockDisplay(b: Block): { icon: string; label: string; color: string; notchColor: string } {
  if (b.kind === 'step') {
    const meta = STEP_TYPE_META[b.stepType]
    if (!meta) return { icon: '❓', label: b.stepType || '未知步骤', color: '#999', notchColor: '#777' }
    return meta
  }
  if (b.kind === 'branch') return { ...FLOW_META.branch, label: `IF: ${b.condition || '条件'}` }
  return { ...FLOW_META.loop, label: `REPEAT ${b.count} 次` }
}

export function blockChildren(b: Block): Block[] {
  if (b.kind === 'branch') return [...b.passChildren, ...b.failChildren]
  if (b.kind === 'loop') return [...b.children]
  return []
}

function emptyStepFields(): Pick<StepBlock, 'xpath' | 'xpath2' | 'timeout' | 'expected_text' | 'index' | 'direction' | 'distance' | 'status'> {
  return {
    xpath: '', xpath2: '', timeout: 10, expected_text: '', index: 0,
    direction: '', distance: 500, status: 'pending',
  }
}

// ═══════════════════════════════════════════
// MOCK DATA
// ═══════════════════════════════════════════

export const MOCK_BLOCKS: Block[] = [
  {
    id: 's1', kind: 'step', stepType: 'wait',
    label: '等待首页加载完成', description: '等待首页加载完成',
    ...emptyStepFields(),
    xpath: '//android.widget.FrameLayout[@resource-id="com.taobao.taobao:id/home"]',
    timeout: 15,
  },
  {
    id: 'b1', kind: 'branch', condition: '搜索结果 > 0?', collapsed: false,
    passChildren: [
      {
        id: 's2', kind: 'step', stepType: 'click',
        label: '点击第一个结果', description: '点击第一个结果',
        ...emptyStepFields(),
        xpath: '//*[@resource-id="result_item"][1]', timeout: 5,
      },
      {
        id: 's3', kind: 'step', stepType: 'verify_text',
        label: '验证商品详情页', description: '验证商品详情页',
        ...emptyStepFields(),
        xpath: '//*[@resource-id="detail_title"]', timeout: 5, expected_text: '商品详情',
      },
    ],
    failChildren: [
      {
        id: 's4', kind: 'step', stepType: 'sleep',
        label: '等待重试', description: '等待重试',
        ...emptyStepFields(), timeout: 2,
      },
    ],
  },
  {
    id: 'l1', kind: 'loop', count: 3, description: '滑动加载更多', collapsed: false,
    children: [
      {
        id: 's5', kind: 'step', stepType: 'sleep',
        label: '等待加载', description: '等待加载',
        ...emptyStepFields(), timeout: 2,
      },
      {
        id: 's6', kind: 'step', stepType: 'swipe',
        label: '向上滑动', description: '向上滑动',
        ...emptyStepFields(), timeout: 3, direction: 'up', distance: 500,
      },
    ],
  },
]
