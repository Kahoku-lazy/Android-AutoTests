/** 元素定位呈现面的纯函数：交互标注文案（缩略图 URL 走共享登记处，组件只做渲染）。 */

/** 七项交互标志的展示口径（与 element-layering 的 flags 键同源、顺序固定） */
export const INTERACTION_FLAGS: Array<{ key: string; label: string }> = [
  { key: "clickable", label: "可点击" },
  { key: "long_clickable", label: "可长按" },
  { key: "scrollable", label: "可滚动" },
  { key: "checkable", label: "可勾选" },
  { key: "checked", label: "已勾选" },
  { key: "enabled", label: "启用" },
  { key: "focusable", label: "可聚焦" },
]

/** 行 → 交互标注标签（只列真值为真的项；空数组表示该元素没有任何交互能力）。 */
export function interactionLabels(row: object): string[] {
  const record = row as Record<string, unknown>
  return INTERACTION_FLAGS.filter((flag) => Boolean(record[flag.key])).map((flag) => flag.label)
}
