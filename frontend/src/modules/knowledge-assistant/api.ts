/**
 * 知识库助手 HTTP 唯一出口：只读就绪状态。
 *
 * WS 不走 axios；浏览器音频通道在 composables/useVoiceSession.ts。
 */
import client from "@/shared/api-client"
import type { DjangoResponse } from "@/shared/api-client"
import type { KnowledgeAssistantStatus } from "./types"
import { KB_STATUS_LOAD_ERROR } from "./constants"

/**
 * 读取知识库助手就绪状态。
 *
 * Returns:
 *   含 enabled / ready / reason / model / voice / log_dir 的状态对象。
 *
 * Raises:
 *   Error: 响应缺少 data 时抛出可读错误。
 */
export async function fetchKnowledgeAssistantStatus(): Promise<KnowledgeAssistantStatus> {
  const response = await client.get<DjangoResponse<KnowledgeAssistantStatus>>(
    "/knowledge-assistant/status/",
  )
  const payload = response.data?.data
  if (!payload) {
    throw new Error(response.data?.message || KB_STATUS_LOAD_ERROR)
  }
  return payload
}
