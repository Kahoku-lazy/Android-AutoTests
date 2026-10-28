/** 平台小助手卡片与新建任务下拉共用的展示列表：一个可见 Agent 一张卡。 */
import type { AgentRecord, RouteConfig } from "@/shared/types/ai"

import { agentDuty, TASK_KIND_CASE_AUTHORING } from "../constants"

export interface AssistantCard {
  key: string
  config?: RouteConfig
  name: string
  agentId: number
  duty: string
}

/** 每个 Agent 渲染一张卡；用例编写 Agent 读 case_authoring 线路，其余读 device_control。 */
export function displayedAssistantCards(agents: AgentRecord[]): AssistantCard[] {
  return (agents || []).map((agent) => {
    const routes = agent.route_configs || {}
    const route =
      agent.task_kind === TASK_KIND_CASE_AUTHORING
        ? routes.case_authoring || routes.device_control
        : routes.device_control
    return {
      key: String(agent.id),
      config: route,
      name: (route?.name || agent.name || "未命名助手").trim(),
      agentId: agent.id,
      duty: agentDuty(agent.task_kind),
    }
  })
}
