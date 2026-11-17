/**
 * 工作流卡片展示字段：把工作流记录与助手名片列表拼成卡片要的名称与笔色。
 *
 * 工作流表不存颜色与名片显示名，卡片每次都按当前名片现算；
 * 名片被删后卡片仍在，用「…已不存在」把缺口说清楚。
 */

import type { AssistantCard, SopWorkflow, SopWorkflowCard } from "../types"

/** 执行助手不存在时的笔色，与后端 `next_marker()` 的首支笔色一致。 */
const FALLBACK_MARKER = "teal"

/**
 * 把工作流记录转成卡片。
 *
 * Args:
 *   workflows: 工作流列表。
 *   cards: 当前助手名片列表，用于取显示名与笔色。
 *
 * Returns:
 *   与 workflows 同序的卡片数组。
 */
export function workflowCards(workflows: SopWorkflow[], cards: AssistantCard[]): SopWorkflowCard[] {
  const byId = new Map(cards.map((card) => [card.assistant_id, card]))
  return workflows.map((workflow) => {
    const executor = byId.get(workflow.executor_assistant_id)
    const verifier = byId.get(workflow.verifier_assistant_id)
    return {
      id: workflow.id,
      name: workflow.name,
      executor_name: executor?.display_name || "执行助手已不存在",
      verifier_name: verifier?.display_name || "验收助手已不存在",
      marker: executor?.marker || FALLBACK_MARKER,
    }
  })
}
