import type { AssistantCard, SopWorkflow, SopWorkflowCard } from "../types"

const FALLBACK_MARKER = "teal"

export function workflowCards(workflows: SopWorkflow[], cards: AssistantCard[]): SopWorkflowCard[] {
  const byId = new Map(cards.map((card) => [card.assistant_id, card]))
  return workflows.map((workflow) => {
    const executor = byId.get(workflow.executor_assistant_id)
    const verifier = byId.get(workflow.verifier_assistant_id)
    const leader = byId.get(workflow.leader_assistant_id || "")
    return {
      id: workflow.id,
      name: workflow.name,
      orchestration: workflow.orchestration || "sop",
      kind: workflow.kind || "ui_automation",
      executor_name: executor?.display_name || "执行助手已不存在",
      verifier_name: verifier?.display_name || "验收助手已不存在",
      leader_name: leader?.display_name || "队长已不存在",
      member_count: workflow.members?.length || 0,
      marker:
        (workflow.orchestration === "team" ? leader?.marker : executor?.marker) || FALLBACK_MARKER,
      release_state: workflow.release_state,
    }
  })
}
