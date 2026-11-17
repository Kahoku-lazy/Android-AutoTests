/** SOP 表单校验。只判断能否提交，不发请求。 */

export interface SopCreateInput {
  name: string
  executorId: string
  verifierId: string
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
  if (!input.executorId) return "先选执行助手"
  if (!input.verifierId) return "先选验收助手"
  return ""
}

export function sameCardAllowed(executorId: string, verifierId: string): boolean {
  return Boolean(executorId) && executorId === verifierId
}

/** 运行输入校验：工作流、当前来源的用例输入与设备都必填。 */
export function sopRunError(input: SopRunInput): string {
  if (!input.workflowId) return "先选一条工作流"
  if (input.source === "platform") {
    if (input.caseCount < 1) return "先选择自动化用例"
  } else if (!input.yamlName.trim()) {
    return "先上传一份里程碑 YAML"
  }
  if (!input.serial.trim()) return "先选择设备"
  return ""
}

/** 成功提示：正文与行动入口文案分开给，链接由调用方挂上，本函数不跳转。 */
export function sopSubmittedMessage(taskId: number): { text: string; action: string } {
  return { text: `已提交，任务 ${taskId}。`, action: "去任务清单" }
}

/** 运行请求带工作流编号、YAML 与必选设备。 */
export function sopRunFields(input: SopRunInput): string[] {
  return ["workflow_id", "config", "device_serial"]
}
