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
  let bgRefreshTimer: ReturnType<typeof setTimeout> | null = null

  /** 切走后仍在后台生成的回复：轮询拉取，直到 assistant 回复落库或放弃。 */
  function scheduleBgRefresh(id: number, retriesLeft: number) {
    bgRefreshTimer = setTimeout(async () => {
      bgRefreshTimer = null
      if (activeConv.value !== id) return
      try {
        const data = await getMessages(id)
        const msgs = data.data?.messages
        if (!data.status || !Array.isArray(msgs)) return
        const last = msgs[msgs.length - 1] as { role?: string } | undefined
        messageStore.hydrateMessages(msgs)
        if (last && last.role === 'user' && retriesLeft > 1) {
          scheduleBgRefresh(id, retriesLeft - 1)
        }
      } catch (e) { logError('Failed to refresh background messages', e, 'useConversation') }
    }, 3000)
  }

  async function loadConversations() {
    try {
      const data = await listConversations(agentIdRef.value)
      if (data.status) conversations.value = data.data?.conversations || []
    } catch (e) { logError('Failed to load conversations', e, 'useConversation') }
  }

  async function newChat(onSelect?: (id: number) => Promise<void>) {
    try {
      const data = await apiCreateConversation(agentIdRef.value, '新对话')
      const payload = data.data
      if (data.status && payload?.id) {
        conversations.value.unshift({
          id: payload.id,
          title: '新对话',
          status: 'active',
        })
        connectionMode.value = 'sse'
        if (onSelect) await onSelect(payload.id)
      }
    } catch (e) {
      connectionMode.value = 'unknown'
      logError('Failed to create conversation', e, 'useConversation')
      ElMessage.error('创建对话失败')
    }
  }

  async function selectChat(id: number, { onAfterSelect }: { onAfterSelect?: (id: number) => Promise<void> } = {}) {
    activeConv.value = id
    if (bgRefreshTimer) { clearTimeout(bgRefreshTimer); bgRefreshTimer = null }
    try {
      const data = await getMessages(id)
      if (data.status) {
        connectionMode.value = 'sse'

        // Always hydrate from DB — the backend persists AI replies for
        // background streams, so DB is always the source of truth.
        const msgs = data.data?.messages
        if (Array.isArray(msgs)) {
          messageStore.hydrateMessages(msgs)
        } else {
          messageStore.clearMessages()
        }

        // Last message is still a user message → a background stream may be
        // generating its reply. Poll until the assistant reply lands.
        const list = Array.isArray(msgs) ? msgs : []
        const last = list[list.length - 1] as { role?: string } | undefined
        if (last && last.role === 'user' && activeConv.value === id) {
          scheduleBgRefresh(id, 10)
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
        if (c) c.title = data.data?.title || title
      }
    } catch (e) { logError('Failed to rename conversation', e, 'useConversation'); ElMessage.error('重命名失败，请稍后重试') }
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
      // ElMessageBox.confirm rejection lands here — ignore. Real errors must reach the user.
      if (e !== 'cancel' && e !== 'close') {
        logError('Failed to delete conversation', e, 'useConversation')
        ElMessage.error('删除失败，请稍后重试')
      }
    }
  }

  return {
    conversations, activeConv, connectionMode, editingConvId, editingTitle,
    loadConversations, newChat, selectChat, startRename, finishRename, cancelRename, deleteConversation,
  }
}
