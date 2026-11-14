/** 编排卡片的纯函数：新旧判定与上线日期文案（无状态，便于单测） */

import type { WorkflowCard } from "../types"

/**
 * 找出上线日期最新的编排键。
 *
 * 日期是 `YYYY-MM-DD` 字符串，可直接按字典序比较；没有日期的卡片不参与。
 *
 * @param cards 编排卡片列表
 * @returns 最新卡片的 key；都没有日期时返回空串
 */
export function newestWorkflowKey(cards: WorkflowCard[]): string {
  let newestKey = ""
  let newestStamp = ""
  for (const card of cards) {
    const stamp = card.released_at || ""
    if (stamp > newestStamp) {
      newestStamp = stamp
      newestKey = card.key
    }
  }
  return newestKey
}

/**
 * 拼卡片的上线日期文案。
 *
 * @param card 编排卡片
 * @returns 形如 `上线于 2026-11-14`；没有日期时返回空串
 */
export function releasedLabel(card: WorkflowCard): string {
  return card.released_at ? `上线于 ${card.released_at}` : ""
}
