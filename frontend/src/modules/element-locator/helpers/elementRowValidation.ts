/**
 * 元素行逐列校验 —— 与后端 apps/element_locator/element_fields.py 同口径的纯函数。
 * 前端校验负责即时提示；后端校验才是防线（见变更 rework-save-to-elements 设计 D6）。
 */

/** `[x1,y1][x2,y2]`，四段均为整数（新增一行的去重键格式） */
export const BOUNDS_PATTERN = /^\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]$/

/** 与 models.Element 列宽对齐（长度校验的唯一真相源；只保留收敛后的可写文本字段） */
export const TEXT_MAX_LENGTH: Record<string, number> = {
  alias: 500,
  text_val: 2000,
  primary_xpath: 2000,
  resource_id: 500,
}

/** 需要长度校验的文本字段：表格行可编辑的三列 + 新增表单的去重键 resource-id */
export type TextField = 'alias' | 'text_val' | 'primary_xpath' | 'resource_id'

/** 校验坐标（新增一行的去重键）：返回中文原因或 null。 */
export function validateBounds(value: string): string | null {
  const text = (value ?? '').trim()
  if (!BOUNDS_PATTERN.test(text)) return '坐标格式应为 [x1,y1][x2,y2]'
  const match = BOUNDS_PATTERN.exec(text)
  if (!match) return '坐标格式应为 [x1,y1][x2,y2]'
  const x1 = Number(match[1])
  const y1 = Number(match[2])
  const x2 = Number(match[3])
  const y2 = Number(match[4])
  if (x2 < x1 || y2 < y1) return '坐标右下角不能小于左上角'
  return null
}

/** 校验元素名称列：返回中文原因或 null（与后端 alias 非空校验同口径）。 */
export function validateAlias(value: string): string | null {
  return (value ?? '').trim() ? null : '元素名称不能为空'
}

/** 校验主定位列：返回中文原因或 null。 */
export function validatePrimaryXPath(value: string): string | null {
  return (value ?? '').trim() ? null : '主定位表达式不能为空'
}

/** 校验文本列：返回中文原因或 null。 */
export function validateText(field: TextField, value: string): string | null {
  const limit = TEXT_MAX_LENGTH[field]
  if (limit != null && (value ?? '').length > limit) return `${field} 最长 ${limit} 个字符`
  return null
}

/** 元素名称单元格：必填 + 不超模型列宽（表格行内编辑的口径） */
export function validateAliasCell(value: string): string | null {
  return validateAlias(value) ?? validateText('alias', value)
}
