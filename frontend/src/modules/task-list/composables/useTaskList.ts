/** 任务列表 — 加载 / 刷新 / 按线路筛选 / 运行态轮询（离开页面即停） */
import { ref, computed, onActivated, onDeactivated, onMounted, onUnmounted } from "vue"
import { ElMessage } from "element-plus"
import { listTasks, deleteTask, clearTasks, rerunTask, cancelTask } from "../api/tasks"
import { useFilterTabs } from "@/shared/composables/useFilterTabs"
import {
  TASK_FILTER_TABS,
  TASK_STATUS_GROUPS,
  TASK_STATUS_GROUPS_DEFAULT_OPEN,
  taskStatusTone,
  type TaskStatusTone,
} from "../constants"
import type { TaskRecord } from "@/shared/types/ai"

/** 运行态轮询间隔：任务执行中每 10s 刷新，全部终态后自动停止 */
const POLL_INTERVAL_MS = 10000

const TERMINAL_STATUSES = new Set(["completed", "success", "failed", "cancelled", "paused"])

export function useTaskList() {
  const tasks = ref<TaskRecord[]>([])
  const loading = ref(false)
  const error = ref("")
  const rerunningId = ref<number | null>(null)
  const cancellingId = ref<number | null>(null)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  // 在途请求计数：轮询在上一轮未返回时直接跳过，避免慢请求叠加
  let inFlight = 0
  // 失活标记：keep-alive 只触发 onDeactivated，离开页面后不得继续轮询
  let deactivated = false
  // onActivated 首次触发紧跟 onMounted，用它区分「首次挂载」与「从缓存回来」
  let activatedOnce = false

  const { activeFilter, filterTabs, filteredItems } = useFilterTabs(
    tasks,
    TASK_FILTER_TABS,
    () => true,
  )

  const groupedByStatus = computed(() =>
    TASK_STATUS_GROUPS.map((group) => ({
      ...group,
      items: filteredItems.value.filter((t: TaskRecord) => taskStatusTone(t.status) === group.key),
    })).filter((group) => group.items.length > 0),
  )

  const expandedGroups = ref<TaskStatusTone[]>([...TASK_STATUS_GROUPS_DEFAULT_OPEN])

  const emptyCopy = computed(() => {
    if (!tasks.value.length) {
      return { text: "还没有任务", hint: "点击「新建任务」创建" }
    }
    return { text: "该分类下还没有任务", hint: "切换分类或新建对应线路的任务" }
  })

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function schedulePoll() {
    stopPoll()
    // 页面已被缓存：不再排定时器，回到页面时由 onActivated 重新加载并重排
    if (deactivated) return
    const hasActive = tasks.value.some(
      (t) => !TERMINAL_STATUSES.has((t.status || "").toLowerCase()),
    )
    if (hasActive) {
      pollTimer = setInterval(() => load(true), POLL_INTERVAL_MS)
    }
  }

  async function load(silent = false) {
    if (silent && inFlight > 0) return
    inFlight += 1
    if (!silent) loading.value = true
    error.value = ""
    try {
      const data = await listTasks()
      if (data.status && data.data) {
        tasks.value = data.data.tasks
        schedulePoll()
      } else {
        error.value = data.message || "加载失败"
      }
    } catch {
      error.value = "加载任务列表失败，请检查网络连接"
    } finally {
      inFlight -= 1
      loading.value = false
    }
  }

  async function remove(task: TaskRecord) {
    try {
      const data = await deleteTask(task.id)
      if (data.status) {
        tasks.value = tasks.value.filter((t) => t.id !== task.id)
        schedulePoll()
        ElMessage.success("已删除")
      } else {
        ElMessage.error(data.message || "删除失败")
      }
    } catch {
      ElMessage.error("删除失败，请检查网络连接")
    }
  }

  async function clearAll() {
    try {
      const data = await clearTasks()
      if (data.status) {
        tasks.value = []
        stopPoll()
        ElMessage.success("已清空任务卡片")
      } else {
        ElMessage.error(data.message || "清空失败")
      }
    } catch {
      ElMessage.error("清空失败，请检查网络连接")
    }
  }

  async function rerun(task: TaskRecord) {
    if (rerunningId.value != null) return
    if (taskStatusTone(task.status) !== "failed") {
      ElMessage.warning("仅失败任务可重新执行")
      return
    }
    rerunningId.value = task.id
    try {
      const data = await rerunTask(task.id)
      if (data.status) {
        ElMessage.success("已新建任务并重新执行")
        await load(true)
      } else {
        ElMessage.error(data.message || "重新执行失败")
      }
    } catch {
      ElMessage.error("重新执行失败，请检查网络连接")
    }
    rerunningId.value = null
  }

  async function cancel(task: TaskRecord) {
    if (cancellingId.value != null) return
    if (taskStatusTone(task.status) !== "running") {
      ElMessage.warning("只有运行中的任务可以关闭")
      return
    }
    cancellingId.value = task.id
    try {
      const data = await cancelTask(task.id)
      if (data.status) {
        ElMessage.success("已关闭任务")
        await load(true)
      } else {
        ElMessage.error(data.message || "关闭失败")
      }
    } catch {
      ElMessage.error("关闭失败，请检查网络连接")
    }
    cancellingId.value = null
  }

  onMounted(load)
  onDeactivated(() => {
    deactivated = true
    stopPoll()
  })
  onActivated(() => {
    // 首次激活紧跟 onMounted，此时 onMounted 已经拉过，不重复请求
    if (!activatedOnce) {
      activatedOnce = true
      return
    }
    deactivated = false
    // 回到清单：静默补拉一次（成功后 schedulePoll 会按有无运行中任务重排定时器）
    void load(true)
  })
  onUnmounted(stopPoll)

  return {
    tasks,
    loading,
    error,
    load,
    rerunningId,
    cancellingId,
    activeFilter,
    filterTabs,
    filteredItems,
    groupedByStatus,
    expandedGroups,
    emptyCopy,
    remove,
    clearAll,
    rerun,
    cancel,
  }
}
