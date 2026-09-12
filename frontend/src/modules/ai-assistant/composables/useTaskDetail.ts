import { onUnmounted, ref, watch, type Ref } from 'vue'
import { getTask } from '../api/tasks'
import { isTaskTerminal } from '../helpers/task-detail'
import type { TaskDetail } from '@/shared/types/ai'

/** 详情页打开且任务未终态时轮询过程 JSON */
const POLL_INTERVAL_MS = 3000

export function useTaskDetail() {
  const loading = ref(false)
  const error = ref('')
  const detail = ref<TaskDetail | null>(null)
  const lastId = ref<number | null>(null)
  let pollTimer: ReturnType<typeof setInterval> | null = null

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function schedulePoll() {
    stopPoll()
    if (!detail.value || isTaskTerminal(detail.value.status)) return
    pollTimer = setInterval(() => {
      refresh()
    }, POLL_INTERVAL_MS)
  }

  async function refresh() {
    if (lastId.value == null) return
    try {
      const data = await getTask(lastId.value)
      if (data.status && data.data) {
        detail.value = data.data
        error.value = ''
        schedulePoll()
      }
    } catch {
      /* 轮询失败不打断已展示内容 */
    }
  }

  async function load(taskId: number) {
    lastId.value = taskId
    loading.value = true
    error.value = ''
    detail.value = null
    stopPoll()
    try {
      const data = await getTask(taskId)
      if (data.status && data.data) {
        detail.value = data.data
        schedulePoll()
      } else {
        error.value = data.message || '加载失败'
      }
    } catch {
      error.value = '加载任务详情失败，请检查网络连接'
    }
    loading.value = false
  }

  function retry() {
    if (lastId.value != null) load(lastId.value)
  }

  function stop() {
    stopPoll()
  }

  /** 绑定路由 id：变化时重载，卸载时停轮询 */
  function bindRouteId(taskId: Ref<number>) {
    watch(
      taskId,
      (id) => {
        if (Number.isFinite(id) && id > 0) load(id)
      },
      { immediate: true },
    )
    onUnmounted(stop)
  }

  onUnmounted(stop)

  return { loading, error, detail, load, retry, stop, bindRouteId }
}
