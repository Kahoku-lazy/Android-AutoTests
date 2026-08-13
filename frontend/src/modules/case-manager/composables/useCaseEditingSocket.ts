/**
 * useCaseEditingSocket — WebSocket listener for collaborative case editing.
 *
 * Connects to ws/case-editing/{caseId} and listens for 'case_updated' events.
 * When an external actor (e.g. AI) modifies the case, the editor can auto-refresh.
 *
 * Usage:
 *   const { connected } = useCaseEditingSocket(caseId, () => load(), {
 *     isDirty: () => isDirty.value,
 *   });
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { wsUrl } from '@/shared/ws-url'
import { getToken } from '@/shared/auth/token-storage'

export function useCaseEditingSocket(
  caseId: () => string | undefined | null,
  onUpdated: () => void,
  options?: {
    /** 有未保存修改时询问用户，避免静默覆盖 */
    isDirty?: () => boolean
    /** loading/saving 时跳过 */
    shouldIgnore?: () => boolean
  },
) {
  const connected = ref(false)
  let socket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let retries = 0
  const MAX_RETRIES = 5
  let promptOpen = false

  function connect() {
    const id = caseId()
    if (!id || id === 'new') return

    const token = getToken()
    if (!token) return

    const url = wsUrl(`/ws/case-editing/${id}?token=${encodeURIComponent(token)}`)
    socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value = true
      retries = 0
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'case_updated') {
          void handleUpdated()
        }
      } catch {
        // Ignore unparseable messages
      }
    }

    socket.onclose = () => {
      connected.value = false
      socket = null
      // Auto-reconnect with exponential backoff
      if (retries < MAX_RETRIES) {
        const delay = Math.min(1000 * Math.pow(2, retries), 16000)
        retries++
        reconnectTimer = setTimeout(connect, delay)
      }
    }

    socket.onerror = () => {
      // onclose will fire after onerror, triggering reconnect
    }
  }

  async function handleUpdated() {
    if (options?.shouldIgnore?.()) return
    if (options?.isDirty?.()) {
      if (promptOpen) return
      promptOpen = true
      try {
        await ElMessageBox.confirm(
          '此用例已被他人或 AI 更新。是否丢弃本地未保存修改并刷新？',
          '远程更新',
          { confirmButtonText: '刷新', cancelButtonText: '保留本地', type: 'warning' },
        )
        onUpdated()
      } catch {
        // keep local edits
      } finally {
        promptOpen = false
      }
      return
    }
    onUpdated()
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    retries = MAX_RETRIES // prevent reconnect
    if (socket) {
      socket.close()
      socket = null
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  // Reconnect when caseId changes (e.g. navigating between cases)
  watch(() => caseId(), (newId, oldId) => {
    if (newId !== oldId) {
      disconnect()
      retries = 0
      connect()
    }
  })

  return { connected }
}
