/** yaml-case-titles — 浏览器端解析 YAML 用例标题（只读，不替代后端校验） */
import { load } from "js-yaml"

export interface CaseTitleParseResult {
  titles: string[]
  /** 可读错误；成功时为空串 */
  error: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

/**
 * 读取 YAML 根节点的用例标题。
 *
 * 根节点支持单条用例映射或用例列表（与后端一致）；只取非空 `title`。
 * 解析失败、结构不对或缺 title 时返回空列表与可读错误，不抛异常。
 */
export function parseCaseTitles(text: string): CaseTitleParseResult {
  if (!String(text || "").trim()) {
    return { titles: [], error: "YAML 中没有可用用例" }
  }
  let doc: unknown
  try {
    doc = load(text)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { titles: [], error: `YAML 无法解析：${message}` }
  }

  const list = Array.isArray(doc) ? doc : doc == null ? [] : [doc]
  if (!list.length) {
    return { titles: [], error: "YAML 中没有可用用例" }
  }

  const titles: string[] = []
  for (const item of list) {
    if (!isRecord(item)) {
      return { titles: [], error: "YAML 根节点必须是用例列表或单条用例" }
    }
    const title = String(item.title ?? "").trim()
    if (!title) {
      return { titles: [], error: "每条用例都必须有非空 title" }
    }
    titles.push(title)
  }
  return { titles, error: "" }
}
