/** Conversation CRUD + Messages API — TypeScript */
import djangoClient from '@/shared/api-client'
import type {
  ConversationListResponse,
  ConversationCreateResponse,
  MessagesResponse,
  SaveMessageResponse,
} from '@/shared/types/ai'

/** 获取 Agent 的对话列表 */
export async function listConversations(agentId: number): Promise<ConversationListResponse> {
  const { data } = await djangoClient.get<ConversationListResponse>(`/ai/agents/${agentId}/conversations`)
  return data
}

/** 创建新对话 */
export async function createConversation(agentId: number, title: string): Promise<ConversationCreateResponse> {
  const { data } = await djangoClient.post<ConversationCreateResponse>(
    `/ai/agents/${agentId}/conversations/create`,
    { title },
  )
  return data
}

/** 获取对话的消息列表 */
export async function getMessages(convId: number): Promise<MessagesResponse> {
  const { data } = await djangoClient.get<MessagesResponse>(`/ai/conversations/${convId}/messages`)
  return data
}

/** 重命名对话 */
export async function renameConversation(convId: number, title: string): Promise<ConversationCreateResponse> {
  const { data } = await djangoClient.post<ConversationCreateResponse>(
    `/ai/conversations/${convId}/rename`,
    { title },
  )
  return data
}

/** 删除对话 */
export async function deleteConversation(convId: number): Promise<{ ok: boolean; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; error?: string }>(`/ai/conversations/${convId}/delete`)
  return data
}

/** 保存用户消息 */
export async function saveUserMessage(convId: number, content: string): Promise<SaveMessageResponse> {
  const { data } = await djangoClient.post<SaveMessageResponse>(
    `/ai/conversations/${convId}/save-message`,
    { role: 'user', content },
  )
  return data
}

/** 保存 Assistant 消息 */
export async function saveAssistantMessage(
  convId: number,
  payload: {
    role: string; content: string; blocks?: object[]; reason?: string;
    tokens?: number; input_tokens?: number; model_name?: string; flow?: string;
  },
): Promise<SaveMessageResponse> {
  const { data } = await djangoClient.post<SaveMessageResponse>(
    `/ai/conversations/${convId}/save-message`,
    payload,
  )
  return data
}

/** 发送 HITL 确认结果 */
export async function postConfirmResult(convId: number, result: object): Promise<{ ok: boolean; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; error?: string }>(
    `/ai/conversations/${convId}/confirm-result`,
    result,
  )
  return data
}
