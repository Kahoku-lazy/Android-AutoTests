/** useLocatorProjects — 系统锁定的三项目列表（不可新建/删除） */
import { computed, ref } from 'vue'
import { formatApiError } from '@/shared/api-client'
import { listLocatorProjects } from '../api'
import type { LocatorProject } from '../types'

export function useLocatorProjects() {
  const projects = ref<LocatorProject[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isEmpty = computed(() => !loading.value && projects.value.length === 0)

  async function loadProjects() {
    loading.value = true
    try {
      const { data } = await listLocatorProjects()
      if (data.status && Array.isArray(data.data)) {
        error.value = ''
        projects.value = data.data
      } else {
        projects.value = []
        error.value = data.message || '项目列表加载失败'
      }
    } catch (e: unknown) {
      projects.value = []
      error.value = formatApiError(e, '项目列表加载失败')
    } finally {
      loading.value = false
    }
  }

  return {
    projects,
    loading,
    error,
    isEmpty,
    loadProjects,
  }
}
