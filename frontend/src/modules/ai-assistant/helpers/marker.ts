/**
 * AI 助手笔色：把后端分配的 marker 键映射成行内 CSS 变量。
 *
 * 色值只在 `modules/ai-assistant/tokens.css` 登记一次；这里只负责选变量名，
 * 让卡片、配置弹窗与对话页共用同一支笔色。未知键回落到 teal，与后端
 * `next_marker()` 的首支笔色一致。
 */

/** 逐支写全：拼字符串会让样式门禁把 `var(--assistant-marker-)` 当成悬空引用。 */
const MARKER_VARS: Record<string, string> = {
  teal: "var(--assistant-marker-teal)",
  ink: "var(--assistant-marker-ink)",
  amber: "var(--assistant-marker-amber)",
  rose: "var(--assistant-marker-rose)",
  moss: "var(--assistant-marker-moss)",
}

/** 行内样式对象：只写 `--assistant-marker`，浅底与渐变由组件用 color-mix 现算。 */
export function markerVars(marker: string): Record<string, string> {
  return { "--assistant-marker": MARKER_VARS[marker] || MARKER_VARS.teal }
}
