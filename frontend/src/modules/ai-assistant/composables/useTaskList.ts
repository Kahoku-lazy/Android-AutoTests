/** 任务列表 — 加载 / 刷新 */
import { ref, onMounted } from 'vue'
import { listTasks } from '../api/tasks'
import type { TaskRecord } from '@/shared/types/ai'

export function useTaskList() {
  const tasks = ref<TaskRecord[]>([])
  const loading = ref(false)
  const error = ref('')

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

  return { tasks, loading, error, load }
}
