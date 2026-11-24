export interface SopCreateInput {
  name: string
  orchestration: "sop" | "goal" | "team"
  executorId: string
  verifierId: string
  leaderId: string
  members: { assistantId: string; description: string }[]
}

export interface SopRunInput {
  workflowId: number | null
  source: "yaml" | "platform"
  yamlName: string
  caseCount: number
  serial: string
}

export function sopCreateError(input: SopCreateInput): string {
  if (!input.name.trim()) return "给这条工作流起个名字"
  if (input.orchestration === "team") {
    if (!input.leaderId) return "先选队长"
    if (input.members.length < 2) return "团队至少需要两名成员"
    if (input.members.some((item) => !item.assistantId || !item.description.trim())) {
      return "每名成员都要选择名片并写明说明"
    }
    const ids = input.members.map((item) => item.assistantId)
    if (ids.includes(input.leaderId) || new Set(ids).size !== ids.length) {
      return "成员不能重复，也不能与队长相同"
    }
    return ""
  }
  if (!input.executorId) return "先选执行助手"
  if (!input.verifierId) return "先选验收助手"
  return ""
}

export function sameCardAllowed(executorId: string, verifierId: string): boolean {
  return Boolean(executorId) && executorId === verifierId
}

export function sopRunError(input: SopRunInput, kind = "ui_automation"): string {
  if (!input.workflowId) return "先选一条工作流"
  if (kind !== "ui_automation") return ""
  if (input.source === "platform") {
    if (input.caseCount < 1) return "先选择自动化用例"
  } else if (!input.yamlName.trim()) {
    return "先上传一份里程碑 YAML"
  }
  if (!input.serial.trim()) return "先选择设备"
  return ""
}

export function sopSubmittedMessage(taskId: number): { text: string; action: string } {
  return { text: `已提交，任务 ${taskId}。`, action: "去任务清单" }
}

export function sopRunFields(input: SopRunInput): string[] {
  return ["workflow_id", "config", "device_serial"]
}
