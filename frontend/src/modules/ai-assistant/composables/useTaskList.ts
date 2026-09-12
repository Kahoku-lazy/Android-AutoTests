/** 任务列表 — 加载 / 刷新 / 按线路筛选 / 运行态轮询 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listTasks, deleteTask, clearTasks } from '../api/tasks'
import { useFilterTabs } from '@/shared/composables/useFilterTabs'
import {
  TASK_FILTER_TABS,
  TASK_STATUS_GROUPS,
  TASK_STATUS_GROUPS_DEFAULT_OPEN,
  taskStatusTone,
  type TaskStatusTone,
} from '../constants'
import type { TaskRecord } from '@/shared/types/ai'

/** 运行态轮询间隔：任务执行中每 5s 刷新，全部终态后自动停止 */
const POLL_INTERVAL_MS = 5000

const TERMINAL_STATUSES = new Set(['completed', 'success', 'failed', 'cancelled', 'paused'])

export function useTaskList() {
  const tasks = ref<TaskRecord[]>([])
  const loading = ref(false)
  const error = ref('')
  let pollTimer: ReturnType<typeof setInterval> | null = null

  const { activeFilter, filterTabs, filteredItems } = useFilterTabs(
    tasks,
    TASK_FILTER_TABS,
    () => true,
  )

  const groupedByStatus = computed(() =>
    TASK_STATUS_GROUPS
      .map((group) => ({
        ...group,
        items: filteredItems.value.filter(
          (t: TaskRecord) => taskStatusTone(t.status) === group.key,
        ),
      }))
      .filter((group) => group.items.length > 0),
  )

  const expandedGroups = ref<TaskStatusTone[]>([...TASK_STATUS_GROUPS_DEFAULT_OPEN])

  const emptyCopy = computed(() => {
    if (!tasks.value.length) {
      return { text: '还没有任务', hint: '点击「新建任务」创建' }
    }
    return { text: '该分类下还没有任务', hint: '切换分类或新建对应线路的任务' }
  })

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function schedulePoll() {
    stopPoll()
    const hasActive = tasks.value.some(
      (t) => !TERMINAL_STATUSES.has((t.status || '').toLowerCase()),
    )
    if (hasActive) {
      pollTimer = setInterval(() => load(true), POLL_INTERVAL_MS)
    }
  }

  async function load(silent = false) {
    if (!silent) loading.value = true
    error.value = ''
    try {
      const data = await listTasks()
      if (data.status && data.data) {
        tasks.value = data.data.tasks
        schedulePoll()
      } else {
        error.value = data.message || '加载失败'
      }
    } catch {
      error.value = '加载任务列表失败，请检查网络连接'
    }
    loading.value = false
  }

  async function remove(task: TaskRecord) {
    try {
      const data = await deleteTask(task.id)
      if (data.status) {
        tasks.value = tasks.value.filter((t) => t.id !== task.id)
        schedulePoll()
        ElMessage.success('已删除')
      } else {
        ElMessage.error(data.message || '删除失败')
      }
    } catch {
      ElMessage.error('删除失败，请检查网络连接')
    }
  }

  async function clearAll() {
    try {
      const data = await clearTasks()
      if (data.status) {
        tasks.value = []
        stopPoll()
        ElMessage.success('已清空任务卡片')
      } else {
        ElMessage.error(data.message || '清空失败')
      }
    } catch {
      ElMessage.error('清空失败，请检查网络连接')
    }
  }

  onMounted(load)
  onUnmounted(stopPoll)

  return {
    tasks, loading, error, load,
    activeFilter, filterTabs, filteredItems, groupedByStatus, expandedGroups, emptyCopy,
    remove, clearAll,
  }
}
