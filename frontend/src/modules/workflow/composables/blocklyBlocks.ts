/**
 * Register Scratch-style Autotest blocks + palette meta for custom Vue sidebar
 */
import * as Blockly from 'blockly'
import {
  STEP_TYPE_META,
  STEPS_NEED_XPATH,
  STEPS_NEED_TIMEOUT,
  STEPS_NEED_PACKAGE,
} from '@/modules/workflow/types/testCase'

export interface PaletteItem {
  type: string
  icon: string
  label: string
  color: string
  hint?: string
}

export interface PaletteCategory {
  key: string
  name: string
  color: string
  accent: string
  icon: string
  items: PaletteItem[]
}

const CATEGORY_META: Record<string, { color: string; accent: string; icon: string }> = {
  点击操作: { color: '#5b9cf5', accent: '#3d7ce0', icon: '👆' },
  滑动操作: { color: '#a78bfa', accent: '#8b6ee0', icon: '👈' },
  等待操作: { color: '#f0c14a', accent: '#d4a62e', icon: '⏳' },
  断言操作: { color: '#6fba2c', accent: '#52991c', icon: '✓' },
  应用控制: { color: '#19c8b9', accent: '#12a396', icon: '📱' },
  流程控制: { color: '#f5a623', accent: '#d98a0f', icon: '◈' },
  APP性能:  { color: '#f5a623', accent: '#e09515', icon: '⏱️' },
  弹窗检测: { color: '#f5a623', accent: '#e09515', icon: '💬' },
}

let registered = false

export function registerAutotestBlocks(): void {
  if (registered) return
  registered = true

  for (const [stepType, meta] of Object.entries(STEP_TYPE_META)) {
    const typeName = `at_${stepType}`
    const fill = meta.color
    Blockly.Blocks[typeName] = {
      init(this: Blockly.Block) {
        this.appendDummyInput('HDR')
          .appendField(meta.icon + '  ' + meta.label)

        this.appendDummyInput()
          .appendField('描述')
          .appendField(new Blockly.FieldTextInput(meta.label), 'LABEL')

        if (STEPS_NEED_XPATH.has(stepType)) {
          this.appendDummyInput()
            .appendField('定位')
            .appendField(new Blockly.FieldTextInput('填写 XPath…'), 'XPATH')
        }
        if (STEPS_NEED_TIMEOUT.has(stepType)) {
          this.appendDummyInput()
            .appendField('超时')
            .appendField(new Blockly.FieldNumber(stepType === 'sleep' ? 2 : 10, 0, 120), 'TIMEOUT')
            .appendField('秒')
        }
        if (STEPS_NEED_PACKAGE.has(stepType)) {
          this.appendDummyInput()
            .appendField('包名')
            .appendField(new Blockly.FieldTextInput('com.example.app'), 'PACKAGE')
        }
        if (['verify_text', 'poll_text'].includes(stepType)) {
          this.appendDummyInput()
            .appendField('期望')
            .appendField(new Blockly.FieldTextInput(''), 'EXPECTED')
        }

        this.setPreviousStatement(true, 'AutotestStep')
        this.setNextStatement(true, 'AutotestStep')
        this.setColour(fill)
        this.setTooltip(meta.label)
        this.setInputsInline(false)
      },
    }
  }

  Blockly.Blocks['at_branch'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('◈  如果')
        .appendField(new Blockly.FieldTextInput('条件成立'), 'CONDITION')
      this.appendStatementInput('THEN')
        .setCheck('AutotestStep')
        .appendField('那么')
      this.appendStatementInput('ELSE')
        .setCheck('AutotestStep')
        .appendField('否则')
      this.setPreviousStatement(true, 'AutotestStep')
      this.setNextStatement(true, 'AutotestStep')
      this.setColour(CATEGORY_META['流程控制'].color)
      this.setTooltip('条件分支')
    },
  }

  Blockly.Blocks['at_loop'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('↻  重复')
        .appendField(new Blockly.FieldNumber(3, 1, 100), 'COUNT')
        .appendField('次')
      this.appendStatementInput('DO')
        .setCheck('AutotestStep')
        .appendField('执行')
      this.setPreviousStatement(true, 'AutotestStep')
      this.setNextStatement(true, 'AutotestStep')
      this.setColour('#a78bfa')
      this.setTooltip('循环')
    },
  }
}

export function getPaletteCategories(): PaletteCategory[] {
  const byCat: Record<string, PaletteItem[]> = {}
  for (const [stepType, meta] of Object.entries(STEP_TYPE_META)) {
    if (!byCat[meta.category]) byCat[meta.category] = []
    byCat[meta.category].push({
      type: `at_${stepType}`,
      icon: meta.icon,
      label: meta.label,
      color: meta.color,
      hint: stepType,
    })
  }

  const order = ['点击操作', '滑动操作', '等待操作', '断言操作', '应用控制', '流程控制', 'APP性能', '弹窗检测']
  const cats: PaletteCategory[] = []

  for (const name of order) {
    const meta = CATEGORY_META[name]
    if (!meta) continue
    const flowBuiltins = name === '流程控制'
      ? [
          { type: 'at_branch', icon: '◈', label: '条件分支', color: meta.color, hint: 'IF / ELSE' },
          { type: 'at_loop', icon: '↻', label: '循环', color: '#a78bfa', hint: 'REPEAT' },
        ]
      : []
    const stepItems = byCat[name] || []
    const items = [...flowBuiltins, ...stepItems]
    if (!items.length) continue
    cats.push({
      key: name,
      name,
      color: meta.color,
      accent: meta.accent,
      icon: meta.icon,
      items,
    })
  }
  return cats
}
