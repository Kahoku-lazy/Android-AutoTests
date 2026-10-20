import { describe, expect, it } from 'vitest'
import { emptySheetRow, validateRow } from '@/modules/case-manager/composables/useCaseSheet'
import { MAX_STEP_TEXT } from '@/modules/case-manager/types'
import type { SheetRowDraft } from '@/modules/case-manager/types'

function draft(overrides: Partial<SheetRowDraft> = {}): SheetRowDraft {
  return { ...emptySheetRow(), title: 'H6810 详情页开关测试', ...overrides }
}

describe('emptySheetRow', () => {
  it('creates a dirty new draft row with enum defaults', () => {
    const row = emptySheetRow()
    expect(row.isNew).toBe(true)
    expect(row.dirty).toBe(true)
    expect(row.id.startsWith('temp-')).toBe(true)
    expect(row.priority).toBe('P1')
    expect(row.system).toBe('ANDROID')
    expect(row.case_type).toBe('AUTO')
    expect(row.business_type).toBe('appliance')
    expect(row.steps).toEqual([])
  })

  it('generates unique temp ids', () => {
    const a = emptySheetRow()
    const b = emptySheetRow()
    expect(a.id).not.toBe(b.id)
  })
})

describe('validateRow', () => {
  it('requires a title', () => {
    expect(validateRow(draft({ title: '  ' }))).toBe('测试标题不能为空')
  })

  it('requires at least one step', () => {
    expect(validateRow(draft())).toBe('执行步骤不能为空')
  })

  it('reports the failing step index for an empty action', () => {
    const row = draft({
      steps: [
        { action: '启动 App', assertion: '进入主页' },
        { action: ' ', assertion: '日志有开灯事件' },
      ],
    })
    expect(validateRow(row)).toBe('第 2 步：动作不能为空')
  })

  it('reports the failing step index for an empty assertion', () => {
    const row = draft({
      steps: [
        { action: '启动 App', assertion: '进入主页' },
        { action: '点击开关', assertion: '' },
      ],
    })
    expect(validateRow(row)).toBe('第 2 步：断言不能为空')
  })

  it('rejects overlong step text', () => {
    const row = draft({
      steps: [{ action: 'x', assertion: 'y'.repeat(MAX_STEP_TEXT + 1) }],
    })
    expect(validateRow(row)).toBe(`第 1 步：断言不能超过 ${MAX_STEP_TEXT} 字符`)
  })

  it('passes a complete step sequence', () => {
    const row = draft({
      steps: [
        { action: '启动 Govee Home App', assertion: '前台为 Govee，进入主页' },
        { action: '点击 H6810 开关按键', assertion: '设备日志出现开灯事件' },
      ],
    })
    expect(validateRow(row)).toBeNull()
  })
})
