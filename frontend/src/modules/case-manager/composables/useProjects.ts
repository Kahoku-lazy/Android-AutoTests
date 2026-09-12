/** useProjects — 项目列表与创建 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import { createProject, deleteProject, listProjects } from '../api'
import type { CaseProject } from '../types'

export function useProjects() {
  const projects = ref<CaseProject[]>([])
  const loading = ref(false)
  const creating = ref(false)
  const error = ref<string | null>(null)

  const isEmpty = computed(() => !loading.value && projects.value.length === 0)

  async function loadProjects() {
    loading.value = true
    error.value = null
    try {
      const { data } = await listProjects()
      if (data.status && Array.isArray(data.data)) {
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

  async function addProject(name: string, description = '') {
    const trimmed = name.trim()
    if (!trimmed) {
      ElMessage.warning('请输入项目名称')
      return null
    }
    creating.value = true
    try {
      const { data } = await createProject({ name: trimmed, description: description.trim() })
      if (data.status && data.data) {
        projects.value = [data.data, ...projects.value]
        ElMessage.success('项目已创建')
        return data.data
      }
      ElMessage.error(data.message || '创建失败')
      return null
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '创建失败'))
      return null
    } finally {
      creating.value = false
    }
  }

  async function removeProject(id: number) {
    try {
      const { data } = await deleteProject(id)
      if (data.status) {
        projects.value = projects.value.filter((p) => p.id !== id)
        ElMessage.success('项目已删除')
        return true
      }
      ElMessage.error(data.message || '删除失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '删除失败'))
      return false
    }
  }

  return {
    projects,
    loading,
    creating,
    error,
    isEmpty,
    loadProjects,
    addProject,
    removeProject,
  }
}
