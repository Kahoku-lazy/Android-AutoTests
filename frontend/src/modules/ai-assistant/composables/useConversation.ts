/** useConversation — 对话列表管理（修复 axios 越层调用） */
import { ref, nextTick, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listConversations,
  createConversation as apiCreateConversation,
  getMessages,
  renameConversation,
  deleteConversation as apiDeleteConversation,
} from '../api/conversations'
import { logError } from '../helpers/logger'
import type { Conversation, ConnectionMode } from '@/shared/types/ai'

export interface UseConversationReturn {
  conversations: Ref<Conversation[]>
  activeConv: Ref<number | null>
  connectionMode: Ref<ConnectionMode>
  editingConvId: Ref<number | null>
  editingTitle: Ref<string>
  loadConversations: () => Promise<void>
  newChat: (onSelect?: (id: number) => Promise<void>) => Promise<void>
  selectChat: (id: number, opts?: { onAfterSelect?: (id: number) => Promise<void> }) => Promise<void>
  startRename: (conv: Conversation) => void
  finishRename: () => Promise<void>
  cancelRename: () => void
  deleteConversation: (conv: Conversation) => Promise<void>
}

interface MessageStoreRef {
  backgroundStreamConvId: Ref<number | null>
  hydrateMessages: (msgs: unknown[]) => void
  clearMessages: () => void
}

export function useConversation(
  agentIdRef: Ref<number>,
  messageStore: MessageStoreRef,
): UseConversationReturn {
  const conversations = ref<Conversation[]>([])
  const activeConv = ref<number | null>(null)
  const connectionMode = ref<ConnectionMode>('unknown')
  const editingConvId = ref<number | null>(null)
  const editingTitle = ref('')

  async function loadConversations() {
    try {
      const data = await listConversations(agentIdRef.value)
      if (data.status) conversations.value = data.conversations
    } catch (e) { logError('Failed to load conversations', e, 'useConversation') }
  }

  async function newChat(onSelect?: (id: number) => Promise<void>) {
    try {
      const data = await apiCreateConversation(agentIdRef.value, '新对话')
      if (data.status) {
        conversations.value.unshift({
          id: data.id,
          title: '新对话',
          status: 'active',
        })
        connectionMode.value = 'sse'
        if (onSelect) await onSelect(data.id)
      }
    } catch (e) {
      connectionMode.value = 'unknown'
      logError('Failed to create conversation', e, 'useConversation')
      ElMessage.error('创建对话失败')
    }
  }

  async function selectChat(id: number, { onAfterSelect }: { onAfterSelect?: (id: number) => Promise<void> } = {}) {
    activeConv.value = id
    try {
      const data = await getMessages(id)
      if (data.status) {
        connectionMode.value = 'sse'

        if (messageStore.backgroundStreamConvId.value === id) {
          // Don't hydrate — in-memory messages updated by background SSE
        } else {
          messageStore.backgroundStreamConvId.value = null
          if (Array.isArray(data.messages)) {
            messageStore.hydrateMessages(data.messages)
          } else {
            messageStore.clearMessages()
          }
        }
      }
    } catch (e) {
      connectionMode.value = 'unknown'
      logError('Failed to load messages', e, 'useConversation')
      ElMessage.error('加载对话消息失败')
    }
    if (onAfterSelect) await onAfterSelect(id)
  }

  function startRename(conv: Conversation) {
    editingConvId.value = conv.id
    editingTitle.value = conv.title
    nextTick(() => {
      const input = document.querySelector('.conv-rename-input') as HTMLInputElement | null
      if (input) { input.focus(); input.select() }
    })
  }

  async function finishRename() {
    const id = editingConvId.value
    const title = editingTitle.value.trim()
    editingConvId.value = null
    if (!title || !id) return
    try {
      const data = await renameConversation(id, title)
      if (data.status) {
        const c = conversations.value.find(x => x.id === id)
        if (c) c.title = data.title || title
      }
    } catch (e) { logError('Failed to rename conversation', e, 'useConversation') }
  }

  function cancelRename() {
    editingConvId.value = null
  }

  async function deleteConversation(conv: Conversation) {
    try {
      await ElMessageBox.confirm(`删除对话「${conv.title}」？`, '确认删除', {
        confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
      })
      const data = await apiDeleteConversation(conv.id)
      if (data.status) {
        ElMessage.success('已删除')
        if (activeConv.value === conv.id) {
          activeConv.value = null
          messageStore.clearMessages()
        }
        loadConversations()
      }
    } catch (e) {
      // ElMessageBox.confirm rejection lands here — ignore. Real errors log.
      if (e !== 'cancel' && e !== 'close') {
        logError('Failed to delete conversation', e, 'useConversation')
      }
    }
  }

  return {
    conversations, activeConv, connectionMode, editingConvId, editingTitle,
    loadConversations, newChat, selectChat, startRename, finishRename, cancelRename, deleteConversation,
  }
}
