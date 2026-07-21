/**
 * Serialize Blockly workspace ↔ testCaseStore Block tree
 */
import * as Blockly from 'blockly'
import type { Block, StepBlock, StepTypeValue } from '@/modules/workflow/types/testCase'
import { STEP_TYPE_META } from '@/modules/workflow/types/testCase'

function genId(prefix: string, counter: { n: number }): string {
  return prefix + counter.n++
}

export function workspaceToBlocks(ws: Blockly.Workspace): Block[] {
  const counter = { n: 1 }
  // Top blocks that are statement chains (not floating orphaned)
  const tops = ws.getTopBlocks(true).filter(b => !b.outputConnection)
  const result: Block[] = []
  for (const top of tops) {
    let cur: Blockly.Block | null = top
    while (cur) {
      const converted = blocklyBlockToTree(cur, counter)
      if (converted) result.push(converted)
      cur = cur.getNextBlock()
    }
  }
  return result
}

function blocklyBlockToTree(b: Blockly.Block, counter: { n: number }): Block | null {
  const type = b.type
  if (type === 'at_branch') {
    return {
      id: genId('b', counter),
      kind: 'branch',
      condition: b.getFieldValue('CONDITION') || '条件',
      passChildren: statementToList(b.getInputTargetBlock('THEN'), counter),
      failChildren: statementToList(b.getInputTargetBlock('ELSE'), counter),
      collapsed: false,
    }
  }
  if (type === 'at_loop') {
    return {
      id: genId('l', counter),
      kind: 'loop',
      count: Number(b.getFieldValue('COUNT') || 3),
      description: '循环',
      children: statementToList(b.getInputTargetBlock('DO'), counter),
      collapsed: false,
    }
  }
  if (type.startsWith('at_')) {
    const stepType = type.slice(3) as StepTypeValue
    if (!STEP_TYPE_META[stepType]) { console.warn(`[blocklySerializer] Unknown step type "${stepType}" — skipping`); return null }
    const label = b.getFieldValue('LABEL') || STEP_TYPE_META[stepType].label
    const step: StepBlock = {
      id: genId('s', counter),
      kind: 'step',
      stepType,
      label,
      description: label,
      xpath: safeField(b, 'XPATH'),
      xpath2: safeField(b, 'XPATH2'),
      timeout: Number(safeField(b, 'TIMEOUT') || 10),
      expected_text: safeField(b, 'EXPECTED'),
      index: Number(safeField(b, 'INDEX') || 0),
      package_name: safeField(b, 'PACKAGE'),
      direction: '',
      distance: 500,
      status: 'pending',
    }
    return step
  }
  return null
}

function statementToList(first: Blockly.Block | null, counter: { n: number }): Block[] {
  const list: Block[] = []
  let cur = first
  while (cur) {
    const converted = blocklyBlockToTree(cur, counter)
    if (converted) list.push(converted)
    cur = cur.getNextBlock()
  }
  return list
}

function safeField(b: Blockly.Block, name: string): string {
  try {
    const f = b.getField(name)
    return f ? String(b.getFieldValue(name) ?? '') : ''
  } catch {
    return ''
  }
}

/** Load store tree into workspace (clear first) */
export function loadBlocksIntoWorkspace(ws: Blockly.Workspace, blocks: Block[]): void {
  ws.clear()
  if (!blocks.length) return

  let prev: Blockly.Block | null = null
  let y = 20
  for (const block of blocks) {
    const created = treeToBlockly(ws, block)
    if (!created) continue
    if (prev) {
      prev.nextConnection?.connect(created.previousConnection!)
    } else {
      created.moveBy(40, y)
    }
    prev = findChainTail(created)
    y += 40
  }
}

function findChainTail(b: Blockly.Block): Blockly.Block {
  let cur = b
  while (cur.getNextBlock()) cur = cur.getNextBlock()!
  return cur
}

function treeToBlockly(ws: Blockly.Workspace, block: Block): Blockly.Block | null {
  if (block.kind === 'step') {
    const b = ws.newBlock(`at_${block.stepType}`) as Blockly.BlockSvg
    setIf(b, 'LABEL', block.label)
    setIf(b, 'XPATH', block.xpath)
    setIf(b, 'XPATH2', block.xpath2)
    setIf(b, 'TIMEOUT', String(block.timeout))
    setIf(b, 'EXPECTED', block.expected_text)
    setIf(b, 'INDEX', String(block.index))
    setIf(b, 'PACKAGE', block.package_name)
    b.initSvg()
    b.render()
    return b
  }
  if (block.kind === 'branch') {
    const b = ws.newBlock('at_branch') as Blockly.BlockSvg
    setIf(b, 'CONDITION', block.condition)
    b.initSvg()
    b.render()
    attachStatementChain(ws, b, 'THEN', block.passChildren)
    attachStatementChain(ws, b, 'ELSE', block.failChildren)
    return b
  }
  if (block.kind === 'loop') {
    const b = ws.newBlock('at_loop') as Blockly.BlockSvg
    setIf(b, 'COUNT', String(block.count))
    b.initSvg()
    b.render()
    attachStatementChain(ws, b, 'DO', block.children)
    return b
  }
  return null
}

function attachStatementChain(
  ws: Blockly.Workspace,
  parent: Blockly.Block,
  inputName: string,
  children: Block[]
): void {
  if (!children.length) return
  let prev: Blockly.Block | null = null
  for (const child of children) {
    const created = treeToBlockly(ws, child)
    if (!created) continue
    if (!prev) {
      parent.getInput(inputName)?.connection?.connect(created.previousConnection!)
    } else {
      prev.nextConnection?.connect(created.previousConnection!)
    }
    prev = findChainTail(created)
  }
}

function setIf(b: Blockly.Block, field: string, value: string): void {
  if (b.getField(field) && value !== undefined && value !== null) {
    b.setFieldValue(value, field)
  }
}

/** Apply xpath from bridged element onto selected block */
export function applyXpathToSelected(ws: Blockly.Workspace, xpath: string, label?: string): boolean {
  const selected = Blockly.getSelected()
  if (!selected || !(selected instanceof Blockly.BlockSvg)) return false
  if (!selected.getField('XPATH')) return false
  selected.setFieldValue(xpath, 'XPATH')
  if (label && selected.getField('LABEL')) {
    selected.setFieldValue(label, 'LABEL')
  }
  return true
}
