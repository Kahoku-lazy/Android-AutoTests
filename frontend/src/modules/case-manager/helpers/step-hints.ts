/** step-hints — 把一步的执行提示（页面锚点 / 日志证据）收成只读展示行 */
import type { CaseStep } from "../types"

export interface StepHintLine {
  label: string
  text: string
}

/**
 * 汇总一步的执行提示为展示行；没有提示时返回空数组。
 *
 * 锚点按 page / entry / target 顺序用「·」连接；日志证据给出型号、端口与关键词。
 * 只做展示，不参与保存校验。
 */
export function stepHintLines(step: CaseStep): StepHintLine[] {
  const lines: StepHintLine[] = []
  const anchor = step.anchor || {}
  const anchorText = [anchor.page, anchor.entry, anchor.target]
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .join(" · ")
  if (anchorText) lines.push({ label: "页面锚点", text: anchorText })

  const log = step.log
  if (log && String(log.sku || "").trim()) {
    const keywords = (log.keywords || []).map((item) => String(item).trim()).filter(Boolean)
    const tail = keywords.length ? ` · ${keywords.join(" / ")}` : ""
    lines.push({ label: "日志证据", text: `${String(log.sku).trim()} · 端口 ${log.port}${tail}` })
  }
  return lines
}
