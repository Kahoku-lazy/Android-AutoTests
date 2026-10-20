/** 平台小助手卡片与新建任务下拉共用的展示列表。当前只有控制设备这一条。 */
import type { AgentRecord, RouteConfig } from "@/shared/types/ai"

export interface AssistantCard {
  key: "device_control"
  config?: RouteConfig
  name: string
  avatar: string
}

export function displayedAssistantCards(agent: AgentRecord | undefined): AssistantCard[] {
  if (!agent) return []
  const route = agent.route_configs?.device_control
  const fallbackName = agent?.name || "未命名助手"
  const fallbackAvatar = agent?.avatar || agent?.avatar_url || "🤖"
  return [
    {
      key: "device_control",
      config: route,
      name: route?.name || fallbackName,
      avatar: route?.avatar || fallbackAvatar,
    },
  ]
}
