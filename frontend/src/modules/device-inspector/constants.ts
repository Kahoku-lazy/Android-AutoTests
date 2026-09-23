/** device-inspector 模块常量 — 分组定义、元素表列宽与空态文案的唯一真相源 */

/** 每页固定 14 行；本页不提供「显示行数」选择器，但选项集与默认值仍登记在此（L4 分页口径） */
export const PAGE_SIZE_OPTIONS: number[] = [14]
export const DEFAULT_PAGE_SIZE = 14

/**
 * 五个可选分组（固定顺序）——标签与分组色的唯一真相源，后端只提供 key。
 * 内容控件按二级拆分，故三项共用 key='content_widget'，用 sub 区分。
 */
export const LAYER_GROUPS: {
  id: string
  key: string
  sub: string
  label: string
  level: number
  color: string
}[] = [
  { id: 'layout_container', key: 'layout_container', sub: '', label: '布局容器', level: 1, color: '#19c8b9' },
  { id: 'scroll_collection', key: 'scroll_collection', sub: '', label: '滚动·集合容器', level: 1, color: '#e59266' },
  { id: 'content_widget/text', key: 'content_widget', sub: 'text', label: '内容控件·文本', level: 2, color: '#b77dee' },
  { id: 'content_widget/icon', key: 'content_widget', sub: 'icon', label: '内容控件·图标', level: 2, color: '#889df0' },
  { id: 'content_widget/other', key: 'content_widget', sub: 'other', label: '内容控件·其它', level: 2, color: '#f8a6b2' },
]

/** 元素条目是否属于某个分组（一级匹配 + 有二级时再匹配二级） */
export function elementInGroup(el, group) {
  if (!el || !group) return false
  if (el.level1 !== group.key) return false
  return group.sub ? el.level2 === group.sub : true
}

/** 分组计数：取后端摘要里的对应节点（内容控件取二级 children），缺失记 0 */
export function groupCount(summary, group) {
  const groups = summary?.groups || []
  const parent = groups.find(g => g.key === group.key)
  if (!parent) return 0
  if (!group.sub) return parent.count || 0
  const child = (parent.children || []).find(c => c.key === group.sub)
  return child?.count || 0
}

/**
 * 元素表列宽（唯一登记处）——前 FROZEN_COLUMN_COUNT 列为冻结列，必须是显式宽度。
 * 列集合覆盖元素条目的全部可用信息；增删列只改这里。
 */
export const FROZEN_COLUMN_COUNT = 3

export const ELEMENT_COLUMN_WIDTHS = {
  // 冻结列（顺序即展示顺序）
  select: 40,
  thumbnail: 66,
  name: 120,
  // 其余列
  seq: 56,
  className: 150,
  resourceId: 170,
  text: 150,
  contentDesc: 130,
  coords: 150,
  depth: 60,
  indexAttr: 70,
  kind: 100,
  kept: 80,
  flags: 170,
  xpath: 220,
}

/** 元素表最小宽 = 上表各列之和（横向滚动阈值） */
export const TABLE_MIN_WIDTH_PX = Object.values(ELEMENT_COLUMN_WIDTHS)
  .reduce((sum, w) => sum + w, 0)

/** 空表文案：任何无数据情形（未选设备 / 未获取 / 分组无元素）统一这一句 */
export const EMPTY_TEXT = { noDevice: '未选中设备' }

/** 不可用（灰底）按键的统一提示文案：index.vue / CaptureForm.vue 与 store 共用 */
export const KEY_DISABLED_MESSAGE = '按键不可用，请先选择设备'

/** 「保存到元素定位」在未勾选任何元素时的提示文案（入口与弹窗确认共用同一句） */
export const NO_SELECTION_MESSAGE = '至少勾选一个元素才能保存'
