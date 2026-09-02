/** 任务列表 — 加载 / 刷新 / 按线路筛选 */
import { ref, computed, onMounted } from 'vue'
import { listTasks } from '../api/tasks'
import { useFilterTabs } from '@/shared/composables/useFilterTabs'
import { TASK_FILTER_TABS } from '../constants'
import type { TaskRecord } from '@/shared/types/ai'

export function useTaskList() {
  const tasks = ref<TaskRecord[]>([])
  const loading = ref(false)
  const error = ref('')

  const { activeFilter, filterTabs, filteredItems } = useFilterTabs(
    tasks,
    TASK_FILTER_TABS,
    (item: TaskRecord, key: string) => item.route === key,
  )

  const emptyCopy = computed(() => {
    if (!tasks.value.length) {
      return { text: '还没有任务', hint: '点击「新建任务」创建' }
    }
    return { text: '该分类下还没有任务', hint: '切换分类或新建对应线路的任务' }
  })

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const data = await listTasks()
      if (data.status && data.data) {
        tasks.value = data.data.tasks
      } else {
        error.value = data.message || '加载失败'
      }
    } catch {
      error.value = '加载任务列表失败，请检查网络连接'
    }
    loading.value = false
  }

  onMounted(load)

  return {
    tasks, loading, error, load,
    activeFilter, filterTabs, filteredItems, emptyCopy,
  }
}
