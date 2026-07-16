// ═══════════════════════════════════════════
// TEST CASE TYPES — Scratch 风格树形 Block 模型
// ═══════════════════════════════════════════

// ── 14 Step Types ──
export const STEP_TYPE_META: Record<string, { icon: string; label: string; color: string; category: string; notchColor: string }> = {
  click:          { icon: '👆', label: '点击元素',     color: '#5b9cf5', category: '点击操作', notchColor: '#4a8adf' },
  click_indexed:  { icon: '👆', label: '点击第N个',    color: '#5b9cf5', category: '点击操作', notchColor: '#4a8adf' },
  retry_click:    { icon: '🔄', label: '重试点击',     color: '#f5a623', category: '点击操作', notchColor: '#e09515' },
  wait:           { icon: '⏳', label: '等待出现',     color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  wait_disappear: { icon: '👻', label: '等待消失',     color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  wait_either:    { icon: '⑂', label: '等待二选一',   color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  wait_toast:     { icon: '💬', label: '等待Toast',    color: '#f7cd67', category: '等待操作', notchColor: '#e6b830' },
  verify_text:    { icon: '✓', label: '验证文本',     color: '#6fba2c', category: '验证操作', notchColor: '#5a9a20' },
  poll_text:      { icon: '🔍', label: '轮询文本',     color: '#6fba2c', category: '验证操作', notchColor: '#5a9a20' },
  sleep:          { icon: '💤', label: '固定等待',     color: '#8a8a96', category: '工具',     notchColor: '#6a6a76' },
  start_app:      { icon: '📱', label: '启动App',      color: '#19c8b9', category: '应用控制', notchColor: '#14a398' },
  kill_app:       { icon: '💀', label: '杀掉App',      color: '#f87171', category: '应用控制', notchColor: '#e55a5a' },
  restart_app:    { icon: '🔁', label: '重启App',      color: '#a78bfa', category: '应用控制', notchColor: '#8b6ee0' },
  log:            { icon: '📝', label: '打印日志',     color: '#8a8a96', category: '工具',     notchColor: '#6a6a76' },
}

export type StepTypeValue = keyof typeof STEP_TYPE_META

/** Steps that typically need an element locator (xpath) */
export const STEPS_NEED_XPATH = new Set([
  'click', 'click_indexed', 'retry_click',
  'wait', 'wait_disappear', 'wait_either',
  'verify_text', 'poll_text',
])

/** Steps that need package_name */
export const STEPS_NEED_PACKAGE = new Set(['start_app', 'kill_app', 'restart_app'])

/** Steps that show timeout field */
export const STEPS_NEED_TIMEOUT = new Set([
  'click', 'click_indexed', 'retry_click',
  'wait', 'wait_disappear', 'wait_either', 'wait_toast',
  'verify_text', 'poll_text', 'sleep', 'restart_app',
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
  /** App package for start/kill/restart */
  package_name: string
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
  type: string
  xpath: string
  xpath2: string
  timeout: number
  expected_text: string
  index: number
  direction: string
  distance: number
  description: string
  package_name?: string
}

// ── Block helpers ──
export function isContainer(b: Block): b is BranchBlock | LoopBlock {
  return b.kind === 'branch' || b.kind === 'loop'
}

export function blockDisplay(b: Block): { icon: string; label: string; color: string; notchColor: string } {
  if (b.kind === 'step') return STEP_TYPE_META[b.stepType]
  if (b.kind === 'branch') return { ...FLOW_META.branch, label: `IF: ${b.condition || '条件'}` }
  return { ...FLOW_META.loop, label: `REPEAT ${b.count} 次` }
}

export function blockChildren(b: Block): Block[] {
  if (b.kind === 'branch') return [...b.passChildren, ...b.failChildren]
  if (b.kind === 'loop') return [...b.children]
  return []
}

function emptyStepFields(): Pick<StepBlock, 'xpath' | 'xpath2' | 'timeout' | 'expected_text' | 'index' | 'package_name' | 'direction' | 'distance' | 'status'> {
  return {
    xpath: '', xpath2: '', timeout: 10, expected_text: '', index: 0,
    package_name: '', direction: '', distance: 500, status: 'pending',
  }
}

// ═══════════════════════════════════════════
// MOCK DATA
// ═══════════════════════════════════════════

export const MOCK_BLOCKS: Block[] = [
  {
    id: 's1', kind: 'step', stepType: 'start_app',
    label: '启动淘宝 App', description: '启动淘宝 App',
    ...emptyStepFields(), package_name: 'com.taobao.taobao', timeout: 10,
  },
  {
    id: 's2', kind: 'step', stepType: 'wait',
    label: '等待首页加载完成', description: '等待首页加载完成',
    ...emptyStepFields(),
    xpath: '//android.widget.FrameLayout[@resource-id="com.taobao.taobao:id/home"]',
    timeout: 15,
  },
  {
    id: 'b1', kind: 'branch', condition: '搜索结果 > 0?', collapsed: false,
    passChildren: [
      {
        id: 's3', kind: 'step', stepType: 'click',
        label: '点击第一个结果', description: '点击第一个结果',
        ...emptyStepFields(),
        xpath: '//*[@resource-id="result_item"][1]', timeout: 5,
      },
      {
        id: 's4', kind: 'step', stepType: 'verify_text',
        label: '验证商品详情页', description: '验证商品详情页',
        ...emptyStepFields(),
        xpath: '//*[@resource-id="detail_title"]', timeout: 5, expected_text: '商品详情',
      },
    ],
    failChildren: [
      {
        id: 's5', kind: 'step', stepType: 'log',
        label: '记录搜索失败', description: '记录搜索失败',
        ...emptyStepFields(), timeout: 0, expected_text: '搜索无结果',
      },
    ],
  },
  {
    id: 'l1', kind: 'loop', count: 3, description: '滑动加载更多', collapsed: false,
    children: [
      {
        id: 's6', kind: 'step', stepType: 'sleep',
        label: '等待加载', description: '等待加载',
        ...emptyStepFields(), timeout: 2,
      },
      {
        id: 's7', kind: 'step', stepType: 'click',
        label: '向上滑动', description: '向上滑动',
        ...emptyStepFields(),
        xpath: '//*[@resource-id="list"]', timeout: 3, direction: 'up', distance: 500,
      },
    ],
  },
  {
    id: 's8', kind: 'step', stepType: 'log',
    label: '截图保存当前页面', description: '截图保存当前页面',
    ...emptyStepFields(), timeout: 0,
  },
]
