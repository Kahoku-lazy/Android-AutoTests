/** log-evidence — 任务详情页「验收设备日志证据」的纯展示口径（无状态、无 HTTP、不重排）
 *
 * 等级与结论的中文口径集中在这里，组件只渲染；排序与合并的唯一真相源是**服务端**
 * （同毫秒合并为一条、最新时间在最上面），前端只按收到顺序呈现，MUST NOT 再排序或再合并。
 */

import type { TaskLogEvidence, TaskLogEvidenceHit, TaskLogFeature } from "@/shared/types/ai"

/** 证据等级 → 中文标签（`periodic` 不能单独作为通过依据，故措辞带「疑似」） */
export const GRADE_LABELS: Record<string, string> = {
  strong: "强证据",
  periodic: "疑似周期",
  before_action: "动作前",
  out_of_window: "超窗",
}

/** 证据结论 → 中文文案 */
export const CONCLUSION_LABELS: Record<string, string> = {
  hit: "窗口内命中",
  no_hit: "有日志但未命中关键词",
  no_log: "窗口内没有日志",
  out_of_window: "仅有超窗日志（晚于动作 + 阈值）",
}

/** 无证据对象时的说明（端口未监听 / 监听已关闭 / 老任务无该字段） */
export const NO_EVIDENCE_TEXT = "本次未采集到设备日志证据（端口未监听或历史任务无该字段）"

export function gradeLabel(grade?: string): string {
  return GRADE_LABELS[String(grade || "")] || String(grade || "未知等级")
}

/** 等级标签的样式类（沿用平台状态色，不新造颜色） */
export function gradeTagClass(grade?: string): string {
  switch (String(grade || "")) {
    case "strong":
      return "sle-tag--strong"
    case "periodic":
      return "sle-tag--periodic"
    case "before_action":
      return "sle-tag--before"
    default:
      return "sle-tag--out"
  }
}

export function conclusionText(conclusion?: string): string {
  return CONCLUSION_LABELS[String(conclusion || "")] || ""
}

/** 功能点文案：`关闭设备成功（#1 设备开关）`；信息不全时降级为可用部分 */
export function featureText(feature?: TaskLogFeature): string {
  const name = String(feature?.feature || "").trim()
  const module = String(feature?.module || "").trim()
  const id = feature?.id
  const suffix = [id === undefined || id === null ? "" : `#${id}`, module].filter(Boolean).join(" ")
  if (name && suffix) return `${name}（${suffix}）`
  return name || suffix || "未登记功能点"
}

/** 一条命中的功能点串（多个全列，不省略） */
export function hitFeatureText(hit?: TaskLogEvidenceHit): string {
  const features = hit?.features || []
  if (!features.length) return ""
  return features.map((item) => featureText(item)).join(" / ")
}

/**
 * 摘要文案：等级 + 条数 + 关键词 + 功能点。
 *
 * 例：`强证据 1 条 · switch_off · 关闭设备成功（#1 设备开关）`；命中多条时逐条列出。
 * 没有命中时给出「未命中 / 无日志」的可读说明，不返回空串（除非压根没有证据对象）。
 */
export function evidenceSummary(evidence?: TaskLogEvidence | null): string {
  if (!evidence) return ""
  const hits = evidence.hits || []
  if (hits.length) {
    return hits
      .map((hit) => {
        const parts = [
          `${gradeLabel(hit.grade)} ${Number(hit.count ?? hit.occurrences?.length ?? 0) || 1} 条`,
          String(hit.keyword || "").trim(),
          hitFeatureText(hit),
        ].filter(Boolean)
        return parts.join(" · ")
      })
      .join("；")
  }
  const conclusion = conclusionText(evidence.conclusion)
  const lines = Number(evidence.window_line_count ?? evidence.lines?.length ?? 0) || 0
  if (conclusion) return `${conclusion}（窗口内 ${lines} 行）`
  return lines ? `窗口内 ${lines} 行日志，未命中关键词` : "窗口内没有日志"
}

/** 是否有可展开的详情（命中 / 动作前 / 超窗 / 原始日志任一非空） */
export function hasEvidenceDetail(evidence?: TaskLogEvidence | null): boolean {
  if (!evidence) return false
  return Boolean(
    (evidence.hits || []).length ||
    (evidence.before_action || []).length ||
    (evidence.out_of_window || []).length ||
    (evidence.lines || []).length,
  )
}

/** 命中列表（原样返回，不排序） */
export function hitList(evidence?: TaskLogEvidence | null): TaskLogEvidenceHit[] {
  return evidence?.hits || []
}

/** 那一刻的原文：优先 `occurrences`，缺失时退回同长度的 `timestamps`（只有时间可展示） */
export function hitOccurrences(
  hit?: TaskLogEvidenceHit,
): Array<{ timestamp: string; text: string; source: string }> {
  const occurrences = hit?.occurrences || []
  if (occurrences.length) {
    return occurrences.map((item) => ({
      timestamp: String(item.timestamp || ""),
      text: String(item.text || ""),
      source: String(item.source || ""),
    }))
  }
  return (hit?.timestamps || []).map((stamp) => ({
    timestamp: String(stamp || ""),
    text: "",
    source: "",
  }))
}

/** 超窗行的展示文案：`16:54:31.460 · +14.309s · 原文` */
export function outOfWindowLine(item?: {
  timestamp?: string
  text?: string
  delta_seconds?: number
}): string {
  const delta = item?.delta_seconds
  const deltaText = typeof delta === "number" ? `+${delta.toFixed(3)}s` : ""
  return [String(item?.timestamp || ""), deltaText, String(item?.text || "")]
    .filter(Boolean)
    .join(" · ")
}

/** 窗口原始日志（原样返回，不排序、不再合并） */
export function evidenceLines(evidence?: TaskLogEvidence | null): Array<{
  timestamp: string
  source: string
  text: string
  merged: boolean
}> {
  return (evidence?.lines || []).map((line) => {
    const text = String(line.text || "")
    return {
      timestamp: String(line.timestamp || ""),
      source: String(line.source || ""),
      text,
      merged: text.includes("\n"),
    }
  })
}

/** 窗口参数说明：`动作 15:47:41.466 起 5 秒内取证（基线 30 秒）` */
export function windowHint(evidence?: TaskLogEvidence | null): string {
  if (!evidence) return ""
  const action = String(evidence.action_times?.[0] || evidence.action_time || "")
  const threshold = evidence.threshold_seconds
  const baseline = evidence.baseline_seconds
  const bits: string[] = []
  if (action) bits.push(`动作 ${action}`)
  if (typeof threshold === "number") bits.push(`取证窗 ${threshold} 秒`)
  if (typeof baseline === "number") bits.push(`动作前基线 ${baseline} 秒`)
  return bits.join(" · ")
}
