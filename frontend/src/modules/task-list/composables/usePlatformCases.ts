/** usePlatformCases — 平台用例选择器数据：项目 → 用例表 → 用例 */
import { ref } from "vue"
import { formatApiError } from "@/shared/api-client"
import { getFileSheet, getProjectTree, listProjects } from "@/modules/case-manager/api"
import type { TreeNode } from "@/modules/case-manager/types"

export interface PlatformProjectOption {
  id: number
  name: string
}

export interface PlatformFileOption {
  id: number
  name: string
}

export interface PlatformCaseOption {
  id: string
  title: string
  stepCount: number
}

/** 把目录树拍平成文件列表（目录只用于分组，选择器按文件取用例） */
export function flattenFiles(nodes: TreeNode[]): PlatformFileOption[] {
  const files: PlatformFileOption[] = []
  for (const node of nodes) {
    if (node.type === "file") {
      files.push({ id: node.id, name: node.name })
      continue
    }
    if (node.children?.length) files.push(...flattenFiles(node.children))
  }
  return files
}

export function usePlatformCases() {
  const projects = ref<PlatformProjectOption[]>([])
  const files = ref<PlatformFileOption[]>([])
  const cases = ref<PlatformCaseOption[]>([])
  const projectId = ref<number | null>(null)
  const fileId = ref<number | null>(null)
  const loading = ref(false)
  const error = ref("")

  async function loadProjects() {
    try {
      const { data } = await listProjects()
      const rows = data.status && Array.isArray(data.data) ? data.data : []
      projects.value = rows.map((item) => ({ id: item.id, name: item.name }))
      if (error.value) error.value = ""
    } catch (err: unknown) {
      projects.value = []
      error.value = formatApiError(err as never, "用例项目加载失败")
    }
  }

  async function loadFiles(nextProjectId: number | null) {
    projectId.value = nextProjectId
    files.value = []
    cases.value = []
    fileId.value = null
    if (nextProjectId == null) return
    loading.value = true
    try {
      const { data } = await getProjectTree(nextProjectId)
      files.value = data.status && data.data ? flattenFiles(data.data.tree || []) : []
      error.value = ""
    } catch (err: unknown) {
      files.value = []
      error.value = formatApiError(err as never, "用例表加载失败")
    }
    loading.value = false
  }

  async function loadCases(nextFileId: number | null) {
    fileId.value = nextFileId
    cases.value = []
    if (nextFileId == null) return
    loading.value = true
    try {
      const { data } = await getFileSheet(nextFileId)
      const rows = data.status && data.data ? data.data.rows || [] : []
      cases.value = rows.map((row) => ({
        id: row.id,
        title: row.title,
        stepCount: row.step_count,
      }))
      error.value = ""
    } catch (err: unknown) {
      cases.value = []
      error.value = formatApiError(err as never, "用例列表加载失败")
    }
    loading.value = false
  }

  function reset() {
    projects.value = []
    files.value = []
    cases.value = []
    projectId.value = null
    fileId.value = null
    error.value = ""
  }

  return {
    projects,
    files,
    cases,
    projectId,
    fileId,
    loading,
    error,
    loadProjects,
    loadFiles,
    loadCases,
    reset,
  }
}
