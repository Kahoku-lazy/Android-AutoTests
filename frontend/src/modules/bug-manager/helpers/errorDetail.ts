/**
 * BUG 详情「错误内容」正文的行解析 — 把「标签：值」型行拆成可加粗的标签与正文。
 *
 * 业务功能：
 * 1. splitErrorDetail: 按行拆分，识别行首短标签（含冒号），其余整行当正文。
 */

/** 一行错误正文的展示结构 */
export interface ErrorDetailLine {
  /** 行首标签，含冒号原文（如「来源任务：」）；无标签时为空串 */
  label: string
  /** 冒号之后的正文；无标签时为整行原文 */
  text: string
}

/**
 * 行首标签：不含空白、冒号与斜杠的最多 12 个字符 + 一个中英冒号。
 * 排除斜杠是为了不把 URL（`https:`）与路径（`C:/`）的协议段当标签。
 */
const LABEL_RE = /^([^\s：:/]{1,12}[：:])[ \t]?(.*)$/

/**
 * 把 BUG 详情的自由文本拆成「标签 + 正文」行。
 *
 * Args:
 *   text: 后端返回的 `detail`（或列表页的 `detail_preview`）原文，可能含换行。
 *
 * Returns:
 *   每行一条 `ErrorDetailLine`；无冒号标签的行 `label` 为空串、`text` 为整行原文。
 */
export function splitErrorDetail(text: string): ErrorDetailLine[] {
  if (!text) return []
  return text.split(/\r?\n/).map((line) => {
    const matched = LABEL_RE.exec(line)
    // 冒号后紧跟 "//" 的是 URL 协议段（https://…），不是标签
    if (!matched || matched[2].startsWith("//")) return { label: "", text: line }
    return { label: matched[1], text: matched[2] }
  })
}
