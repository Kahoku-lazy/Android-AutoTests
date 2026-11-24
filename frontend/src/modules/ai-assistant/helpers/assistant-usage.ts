/** 删除助手前的占用检查：纯判断，不发请求。 */

import type { SopWorkflow } from "../types"

/**
 * 找出把该助手用作执行、验收、队长或成员的工作流名称。
 * 同一条工作流只计一次，按传入顺序返回。
 */
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

/** 占用提示：点名到具体工作流，多条用顿号连接。 */
export function assistantInUseMessage(names: string[]): string {
  return `该助手正被工作流「${names.join("、")}」使用，请先解除绑定再删除。`
}
