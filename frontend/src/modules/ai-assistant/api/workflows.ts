/** 单智能体编排：清单与一轮对话。 */
import client from "@/shared/api-client"
import { getToken } from "@/shared/auth/token-storage"

import type { WorkflowCard, WorkflowListResponse } from "../types"

export type { WorkflowCard }

/** 拉取单智能体编排清单；接口返回 {status, data:{workflows}} 信封。 */
export async function listWorkflows(): Promise<WorkflowCard[]> {
  const { data } = await client.get<WorkflowListResponse>("/ai/workflows/")
  return data.data?.workflows ?? []
}

/** 读取一次会话在本地事件日志里的模型事件行。 */
export async function fetchWorkflowEvents(sessionId: string): Promise<string[]> {
  const { data } = await client.get<{ status: boolean; data?: { events?: string[] } }>(
    "/ai/workflows/events/",
    { params: { session: sessionId } },
  )
  return data.data?.events ?? []
}

/** 向所选编排发送一轮消息，返回本轮文本。 */
export async function sendWorkflowMessage(options: {
  key: string
  serial: string
  message: string
  sessionId: string
}): Promise<string> {
  const token = getToken()
  const response = await window.fetch(`/api/ai/workflows/${options.key}/stream/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      serial: options.serial,
      message: options.message,
      session_id: options.sessionId,
    }),
  })
  if (!response.ok) throw new Error(await response.text())
  const raw = await response.text()
  return raw
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim())
    .join("")
}
