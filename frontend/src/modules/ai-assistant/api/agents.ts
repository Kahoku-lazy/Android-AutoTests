import djangoClient from "@/shared/api-client"
import type { AgentListResponse, AgentDetailResponse } from "@/shared/types/ai"

export async function listAgents(): Promise<AgentListResponse> {
  const { data } = await djangoClient.get<AgentListResponse>("/ai/agents/")
  return data
}

export async function getAgentDetail(agentId: number): Promise<AgentDetailResponse> {
  const { data } = await djangoClient.get<AgentDetailResponse>(`/ai/agents/${agentId}/`)
  return data
}

export async function saveAgent(
  isNew: boolean,
  agentId: number | null,
  payload: object,
): Promise<AgentDetailResponse> {
  const url = isNew ? "/ai/agents/create/" : `/ai/agents/${agentId}/update/`
  const { data } = await djangoClient.post<AgentDetailResponse>(url, payload)
  return data
}
