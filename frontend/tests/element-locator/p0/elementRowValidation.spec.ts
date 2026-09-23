/**
 * [P0] 必测 — 元素行逐列校验纯函数（与后端 element_fields.py 同口径）
 * 目录：tests/element-locator/p0/
 */
import { describe, expect, it } from 'vitest'
import {
  validateAlias,
  validateAliasCell,
  validateBounds,
  validatePrimaryXPath,
  validateText,
} from '@/modules/element-locator/helpers/elementRowValidation'
import {
  INTERACTION_FLAGS,
  elementThumbnailUrl,
  interactionLabels,
} from '@/modules/element-locator/helpers/elementPresentation'

describe('[P0] elementRowValidation', () => {
  it('validateBounds：坐标是新增行的去重键，格式与尺寸非法各给中文原因', () => {
    expect(validateBounds('abc')).toBe('坐标格式应为 [x1,y1][x2,y2]')
    expect(validateBounds('[10,20][5,220]')).toBe('坐标右下角不能小于左上角')
    expect(validateBounds('[0,0][10,10]')).toBeNull()
  })

  it('validatePrimaryXPath：空表达式被拒（主定位是单条表达式）', () => {
    expect(validatePrimaryXPath('   ')).toBe('主定位表达式不能为空')
    expect(validatePrimaryXPath('//a')).toBeNull()
  })

  it('validateAlias / validateAliasCell：元素名称必填，且仍受列宽约束', () => {
    expect(validateAlias('   ')).toBe('元素名称不能为空')
    expect(validateAlias('登录')).toBeNull()
    expect(validateAliasCell(' ')).toBe('元素名称不能为空')
    expect(validateAliasCell('a'.repeat(501))).toBe('alias 最长 500 个字符')
    expect(validateAliasCell('a'.repeat(500))).toBeNull()
  })

  it('validateText：只对收敛后的可写列做长度校验，边界值通过', () => {
    expect(validateText('alias', 'a'.repeat(500))).toBeNull()
    expect(validateText('alias', 'a'.repeat(501))).toBe('alias 最长 500 个字符')
    expect(validateText('text_val', 'x'.repeat(2000))).toBeNull()
    expect(validateText('primary_xpath', 'x'.repeat(2001))).toBe('primary_xpath 最长 2000 个字符')
  })
})

describe('[P0] elementPresentation', () => {
  it('elementThumbnailUrl：有路径才产 /media/ URL', () => {
    expect(elementThumbnailUrl('locator/pages/1/el_a.png')).toBe('/media/locator/pages/1/el_a.png')
    expect(elementThumbnailUrl('')).toBe('')
  })

  it('interactionLabels：七项交互标注只列真值为真的项', () => {
    expect(INTERACTION_FLAGS).toHaveLength(7)
    expect(
      interactionLabels({ clickable: true, enabled: true, focusable: false }),
    ).toEqual(['可点击', '启用'])
    expect(interactionLabels({})).toEqual([])
  })
})
