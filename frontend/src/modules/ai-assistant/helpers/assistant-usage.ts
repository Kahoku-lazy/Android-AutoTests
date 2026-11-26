import type { SopWorkflow } from "../types"

export function workflowsUsingAssistant(assistantId: string, workflows: SopWorkflow[]): string[] {
  const names: string[] = []
  for (const workflow of workflows) {
    const bound = [
      workflow.executor_assistant_id,
      workflow.verifier_assistant_id,
      workflow.leader_assistant_id,
      ...(workflow.members || []).map((member) => member.assistant_id),
    ]
    if (bound.includes(assistantId)) names.push(workflow.name)
  }
  return names
}

export function assistantInUseMessage(names: string[]): string {
  return `该助手正被工作流「${names.join("、")}」使用，请先解除绑定再删除。`
}
