import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Block, StepBlock, BranchBlock, LoopBlock, StepTypeValue } from '@/modules/workflow/types/testCase'
import { MOCK_BLOCKS, STEP_TYPE_META } from '@/modules/workflow/types/testCase'

let nextId = 1

function genId(prefix = 's'): string {
  return prefix + nextId++
}

// ═══════════════════════════════════════════
// RECURSIVE TREE OPERATIONS
// ═══════════════════════════════════════════

function findInList(id: string, blocks: Block[]): Block | null {
  for (const b of blocks) {
    if (b.id === id) return b
    if (b.kind === 'branch') {
      const found = findInList(id, b.passChildren) || findInList(id, b.failChildren)
      if (found) return found
    }
    if (b.kind === 'loop') {
      const found = findInList(id, b.children)
      if (found) return found
    }
  }
  return null
}

function findParent(
  id: string,
  blocks: Block[]
): { list: Block[]; index: number } | null {
  for (let i = 0; i < blocks.length; i++) {
    if (blocks[i].id === id) return { list: blocks, index: i }
    const b = blocks[i]
    if (b.kind === 'branch') {
      const r = findParent(id, b.passChildren)
      if (r) return r
      const r2 = findParent(id, b.failChildren)
      if (r2) return r2
    }
    if (b.kind === 'loop') {
      const r = findParent(id, b.children)
      if (r) return r
    }
  }
  return null
}

function removeFromList(id: string, blocks: Block[]): Block | null {
  const idx = blocks.findIndex(b => b.id === id)
  if (idx >= 0) {
    const [removed] = blocks.splice(idx, 1)
    return removed
  }
  for (const b of blocks) {
    if (b.kind === 'branch') {
      const r = removeFromList(id, b.passChildren) || removeFromList(id, b.failChildren)
      if (r) return r
    }
    if (b.kind === 'loop') {
      const r = removeFromList(id, b.children)
      if (r) return r
    }
  }
  return null
}

function getAllBlocks(blocks: Block[]): Block[] {
  const result: Block[] = []
  for (const b of blocks) {
    result.push(b)
    if (b.kind === 'branch') {
      result.push(...getAllBlocks(b.passChildren))
      result.push(...getAllBlocks(b.failChildren))
    }
    if (b.kind === 'loop') {
      result.push(...getAllBlocks(b.children))
    }
  }
  return result
}

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

// ═══════════════════════════════════════════
// PINIA STORE
// ═══════════════════════════════════════════

export const useTestCaseStore = defineStore('wf-testCase', () => {
  const rootBlocks = ref<Block[]>([])
  const selectedId = ref<string | null>(null)
  const isExecuting = ref(false)
  const executionSpeed = ref(800)
  const statusMessage = ref('从左侧面板点击添加步骤 · 拖拽排序')
  const caseName = ref('未命名用例')
  const packageName = ref('com.example.app')
  /** 关联的 case-manager 用例 id（空=新建） */
  const linkedCaseId = ref<string>('')
  const directoryId = ref<number | null>(null)
  /** 外部加载内容时递增，驱动 Blockly 刷新 */
  const contentRev = ref(0)

  // ── Selection ──
  const selectedBlock = computed(() => {
    if (!selectedId.value) return null
    return findInList(selectedId.value, rootBlocks.value)
  })

  function select(id: string | null): void {
    selectedId.value = id
  }

  // ── Block Factory ──
  function createStepBlock(stepType: StepTypeValue): StepBlock {
    const meta = STEP_TYPE_META[stepType]
    const needsPackage = stepType === 'start_app' || stepType === 'kill_app' || stepType === 'restart_app'
    return {
      id: genId('s'),
      kind: 'step',
      stepType,
      label: meta.label,
      description: meta.label,
      xpath: '',
      xpath2: '',
      timeout: stepType === 'sleep' ? 2 : 10,
      expected_text: '',
      index: 0,
      package_name: needsPackage ? packageName.value : '',
      direction: '',
      distance: 500,
      status: 'pending',
    }
  }

  function createBranchBlock(): BranchBlock {
    return {
      id: genId('b'),
      kind: 'branch',
      condition: '条件',
      passChildren: [],
      failChildren: [],
      collapsed: false,
    }
  }

  function createLoopBlock(): LoopBlock {
    return {
      id: genId('l'),
      kind: 'loop',
      count: 3,
      description: '循环',
      children: [],
      collapsed: false,
    }
  }

  // ── Insert / Remove ──
  function addStepAfter(afterId: string | null, stepType: StepTypeValue): Block {
    const block = createStepBlock(stepType)
    if (!afterId) {
      rootBlocks.value.push(block)
    } else {
      const parent = findParent(afterId, rootBlocks.value)
      if (parent) {
        parent.list.splice(parent.index + 1, 0, block)
      } else {
        rootBlocks.value.push(block)
      }
    }
    select(block.id)
    return block
  }

  function addBranchAfter(afterId: string | null): Block {
    const block = createBranchBlock()
    if (!afterId) {
      rootBlocks.value.push(block)
    } else {
      const parent = findParent(afterId, rootBlocks.value)
      if (parent) {
        parent.list.splice(parent.index + 1, 0, block)
      } else {
        rootBlocks.value.push(block)
      }
    }
    select(block.id)
    return block
  }

  function addLoopAfter(afterId: string | null): Block {
    const block = createLoopBlock()
    if (!afterId) {
      rootBlocks.value.push(block)
    } else {
      const parent = findParent(afterId, rootBlocks.value)
      if (parent) {
        parent.list.splice(parent.index + 1, 0, block)
      } else {
        rootBlocks.value.push(block)
      }
    }
    select(block.id)
    return block
  }

  function removeBlock(id: string): void {
    if (selectedId.value === id) selectedId.value = null
    removeFromList(id, rootBlocks.value)
  }

  // ── Move Block (drag reorder) ──
  function moveBlock(blockId: string, toList: Block[], toIndex: number): void {
    const parent = findParent(blockId, rootBlocks.value)
    if (!parent) return

    // Same-list reorder: adjust index after removal so splice stays correct
    let insertAt = toIndex
    if (parent.list === toList && parent.index < toIndex) {
      insertAt = toIndex - 1
    }

    const [block] = parent.list.splice(parent.index, 1)
    if (!block) return
    // Clamp in case target shrank
    insertAt = Math.max(0, Math.min(insertAt, toList.length))
    toList.splice(insertAt, 0, block)
  }

  // Insert a block from palette drag into a specific position
  function insertBlockAt(block: Block, targetList: Block[], targetIndex: number): void {
    targetList.splice(targetIndex, 0, block)
  }

  // Get the list path to a block's parent (for serialization / drag target resolution)
  function getListPath(blockId: string, blocks: Block[]): string[] {
    const path: string[] = []
    function find(b: Block[]): boolean {
      for (const item of b) {
        if (item.id === blockId) return true
        if (item.kind === 'branch') {
          if (find(item.passChildren)) { path.unshift('passChildren'); return true }
          if (find(item.failChildren)) { path.unshift('failChildren'); return true }
        }
        if (item.kind === 'loop') {
          if (find(item.children)) { path.unshift('children'); return true }
        }
      }
      return false
    }
    find(blocks)
    return path
  }

  // Find which list a block belongs to (for drag source resolution)
  function findBlockList(blockId: string, blocks: Block[]): Block[] | null {
    const parent = findParent(blockId, blocks)
    return parent ? parent.list : null
  }

  // ── Step Data Update ──
  function updateStepData(
    id: string,
    data: Partial<Pick<StepBlock, 'label' | 'description' | 'xpath' | 'xpath2' | 'timeout' | 'expected_text' | 'index' | 'package_name' | 'direction' | 'distance' | 'element_id' | 'element_label'>>
  ): void {
    const block = findInList(id, rootBlocks.value)
    if (block && block.kind === 'step') {
      Object.assign(block, data)
      // Keep description in sync when only label changes
      if (data.label !== undefined && data.description === undefined) {
        block.description = data.label
      }
    }
  }

  function updateBranchCondition(id: string, condition: string): void {
    const block = findInList(id, rootBlocks.value)
    if (block && block.kind === 'branch') {
      block.condition = condition
    }
  }

  function updateLoopData(id: string, count: number): void {
    const block = findInList(id, rootBlocks.value)
    if (block && block.kind === 'loop') {
      block.count = count
    }
  }

  // ── Collapse ──
  function toggleCollapse(id: string): void {
    const block = findInList(id, rootBlocks.value)
    if (block && (block.kind === 'branch' || block.kind === 'loop')) {
      block.collapsed = !block.collapsed
    }
  }

  // ── Wrap / Unwrap ──
  function wrapInBranch(blockIds: string[]): void {
    if (blockIds.length === 0) return
    const branch = createBranchBlock()
    // Sort by current order in the shared parent list (first id wins for insert pos)
    const firstParent = findParent(blockIds[0], rootBlocks.value)
    if (!firstParent) return

    const all = getAllBlocks(rootBlocks.value)
    const toWrap = blockIds.map(id => findInList(id, rootBlocks.value)).filter(Boolean) as Block[]
    toWrap.sort((a, b) => {
      const ia = all.indexOf(a)
      const ib = all.indexOf(b)
      return ia - ib
    })

    // Record insert index from the earliest block still in the same list as first
    let insertIndex = firstParent.index
    for (const b of toWrap) {
      const p = findParent(b.id, rootBlocks.value)
      if (p && p.list === firstParent.list && p.index < insertIndex) {
        insertIndex = p.index
      }
    }

    toWrap.forEach(b => removeFromList(b.id, rootBlocks.value))
    // After removals, clamp insert index into the target list
    insertIndex = Math.max(0, Math.min(insertIndex, firstParent.list.length))
    branch.passChildren = toWrap
    firstParent.list.splice(insertIndex, 0, branch)
    select(branch.id)
  }

  function unwrapBlock(id: string): void {
    const parent = findParent(id, rootBlocks.value)
    if (!parent) return
    const block = parent.list[parent.index]
    if (!block || (block.kind !== 'branch' && block.kind !== 'loop')) return

    const children = block.kind === 'branch'
      ? [...block.passChildren, ...block.failChildren]
      : [...block.children]
    parent.list.splice(parent.index, 1, ...children)
    if (selectedId.value === id) selectedId.value = null
  }

  // ── Execution Simulation ──
  async function startExecution(): Promise<void> {
    if (isExecuting.value) return
    isExecuting.value = true

    const all = getAllBlocks(rootBlocks.value)
    all.forEach(b => { if (b.kind === 'step') b.status = 'pending' })

    for (const block of all) {
      if (!isExecuting.value) break
      if (block.kind !== 'step') continue

      block.status = 'running'
      statusMessage.value = `执行中: ${block.label}`
      await delay(executionSpeed.value / 2)

      const result: 'pass' | 'fail' = Math.random() > 0.15 ? 'pass' : 'fail'
      block.status = result
      statusMessage.value = result === 'pass'
        ? `✅ ${block.label}`
        : `❌ ${block.label} — 失败`
      await delay(executionSpeed.value / 2)

      if (result === 'fail') {
        statusMessage.value = '执行中断: 步骤失败'
        break
      }
    }

    if (isExecuting.value) statusMessage.value = '🎉 测试执行完成'
    isExecuting.value = false
  }

  function stopExecution(): void {
    isExecuting.value = false
  }

  function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // ── Persistence ──
  function loadMock(): void {
    rootBlocks.value = deepClone(MOCK_BLOCKS)
    selectedId.value = null
    packageName.value = 'com.taobao.taobao'
    // Recover nextId
    const all = getAllBlocks(rootBlocks.value)
    let max = 0
    all.forEach(b => {
      const n = parseInt(b.id.replace(/\D/g, ''))
      if (n > max) max = n
    })
    nextId = max + 1
    statusMessage.value = '已加载: 淘宝搜索商品测试'
    caseName.value = '淘宝搜索商品测试'
  }

  function saveToLocal(): void {
    const data = {
      name: caseName.value,
      package_name: packageName.value,
      blocks: rootBlocks.value,
      savedAt: new Date().toISOString(),
    }
    const json = JSON.stringify(data)
    localStorage.setItem('tc_tree_current', json)
    // Named key must match loadByName('tc_tree_' + name)
    localStorage.setItem('tc_tree_' + caseName.value, json)
    const idx = JSON.parse(localStorage.getItem('tc_tree_idx') || '[]')
    if (!idx.includes(caseName.value)) idx.push(caseName.value)
    localStorage.setItem('tc_tree_idx', JSON.stringify(idx))
    statusMessage.value = '已保存: ' + caseName.value
  }

  function loadFromLocal(): boolean {
    const raw = localStorage.getItem('tc_tree_current')
    if (!raw) return false
    const data = JSON.parse(raw)
    rootBlocks.value = data.blocks
    caseName.value = data.name || '加载的用例'
    packageName.value = data.package_name || packageName.value
    selectedId.value = null
    const all = getAllBlocks(rootBlocks.value)
    let max = 0
    all.forEach(b => {
      const n = parseInt(b.id.replace(/\D/g, ''))
      if (n > max) max = n
    })
    nextId = max + 1
    statusMessage.value = '已加载: ' + caseName.value
    return true
  }

  function getLocalList(): string[] {
    return JSON.parse(localStorage.getItem('tc_tree_idx') || '[]')
  }

  function loadByName(name: string): boolean {
    const raw = localStorage.getItem('tc_tree_' + name)
    if (!raw) {
      statusMessage.value = '未找到: ' + name
      return false
    }
    const data = JSON.parse(raw)
    rootBlocks.value = data.blocks
    caseName.value = data.name || name
    packageName.value = data.package_name || packageName.value
    selectedId.value = null
    const all = getAllBlocks(rootBlocks.value)
    let max = 0
    all.forEach(b => {
      const n = parseInt(b.id.replace(/\D/g, ''))
      if (n > max) max = n
    })
    nextId = max + 1
    statusMessage.value = '已加载: ' + caseName.value
    return true
  }

  function deleteSaved(name: string): void {
    localStorage.removeItem('tc_tree_' + name)
    const idx = getLocalList().filter(n => n !== name)
    localStorage.setItem('tc_tree_idx', JSON.stringify(idx))
  }

  function exportJSON(): string {
    return JSON.stringify({ name: caseName.value, blocks: rootBlocks.value }, null, 2)
  }

  function importJSON(json: string): boolean {
    try {
      const data = JSON.parse(json)
      rootBlocks.value = data.blocks || []
      caseName.value = data.name || '导入的用例'
      if (data.package_name) packageName.value = data.package_name
      return true
    } catch {
      statusMessage.value = '导入失败: JSON 格式错误'
      return false
    }
  }

  function clearAll(): void {
    rootBlocks.value = []
    selectedId.value = null
    linkedCaseId.value = ''
    statusMessage.value = '已清空'
  }

  function setStatus(msg: string): void {
    statusMessage.value = msg
  }

  function setPackageName(name: string): void {
    packageName.value = name
  }

  function setLinkedCase(id: string, title?: string, pkg?: string, dirId?: number | null): void {
    linkedCaseId.value = id || ''
    if (title) caseName.value = title
    if (pkg) packageName.value = pkg
    if (dirId !== undefined) directoryId.value = dirId
  }

  function loadStepBlocks(blocks: Block[], meta?: { id?: string; title?: string; packageName?: string; directoryId?: number | null }): void {
    rootBlocks.value = blocks
    selectedId.value = null
    if (meta?.id !== undefined) linkedCaseId.value = meta.id || ''
    if (meta?.title) caseName.value = meta.title
    if (meta?.packageName) packageName.value = meta.packageName
    if (meta?.directoryId !== undefined) directoryId.value = meta.directoryId
    contentRev.value++
    statusMessage.value = `已加载用例「${caseName.value}」· ${stepCount.value} 步`
  }

  // ── Total count ──
  const totalBlocks = computed(() => getAllBlocks(rootBlocks.value).length)
  const stepCount = computed(() => getAllBlocks(rootBlocks.value).filter(b => b.kind === 'step').length)

  function initDemo(): void {
    if (rootBlocks.value.length > 0) return
    loadMock()
  }

  return {
    rootBlocks, selectedId, isExecuting, executionSpeed,
    statusMessage, caseName, packageName, linkedCaseId, directoryId, contentRev,
    selectedBlock, totalBlocks, stepCount,
    select,
    createStepBlock, createBranchBlock, createLoopBlock,
    addStepAfter, addBranchAfter, addLoopAfter, removeBlock,
    moveBlock, insertBlockAt, getListPath, findBlockList,
    updateStepData, updateBranchCondition, updateLoopData,
    toggleCollapse,
    wrapInBranch, unwrapBlock,
    startExecution, stopExecution,
    loadMock, saveToLocal, loadFromLocal, getLocalList, loadByName, deleteSaved,
    exportJSON, importJSON,
    clearAll, setStatus, setPackageName, setLinkedCase, loadStepBlocks,
    initDemo,
    findInList: (id: string) => findInList(id, rootBlocks.value),
    getAllBlocks: () => getAllBlocks(rootBlocks.value),
  }
})
