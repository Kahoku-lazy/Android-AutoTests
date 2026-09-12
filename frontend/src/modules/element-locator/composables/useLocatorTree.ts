/** useLocatorTree — 按项目 code 加载目录树并维护目录/叶子 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import {
  apiCreateApiEndpoint,
  apiCreatePage,
  apiCreateWebElement,
  apiDeleteApiEndpoint,
  apiDeletePage,
  apiDeleteWebElement,
  batchDeleteLocatorFiles,
  createLocatorDirectory,
  deleteLocatorDirectory,
  getLocatorProjectTree,
  moveLocatorItem,
  updateLocatorDirectory,
} from '../api'
import {
  FILE_KIND_BY_CODE,
  isLocatorProjectCode,
  type LocatorFileKind,
  type LocatorProject,
  type LocatorProjectCode,
  type LocatorTreeNode,
} from '../types'

function createdLeafId(payload: Record<string, unknown>): number | null {
  const nested = payload.data
  if (nested && typeof nested === 'object' && nested !== null && 'id' in nested) {
    const id = (nested as { id: unknown }).id
    if (typeof id === 'number') return id
  }
  for (const key of ['page', 'element', 'endpoint'] as const) {
    const node = payload[key]
    if (node && typeof node === 'object' && node !== null && 'id' in node) {
      const id = (node as { id: unknown }).id
      if (typeof id === 'number') return id
    }
  }
  return null
}

export function useLocatorTree(projectCode: () => string) {
  const project = ref<LocatorProject | null>(null)
  const tree = ref<LocatorTreeNode[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  function resolvedCode(): LocatorProjectCode | null {
    const code = projectCode()
    return isLocatorProjectCode(code) ? code : null
  }

  async function loadTree() {
    const code = resolvedCode()
    if (!code) {
      error.value = '未知项目'
      project.value = null
      tree.value = []
      return
    }
    loading.value = true
    try {
      const { data } = await getLocatorProjectTree(code)
      if (data.status && data.data) {
        error.value = ''
        project.value = data.data.project
        tree.value = data.data.tree || []
      } else {
        error.value = data.message || '目录树加载失败'
      }
    } catch (e: unknown) {
      error.value = formatApiError(e, '目录树加载失败')
    } finally {
      loading.value = false
    }
  }

  async function addDirectory(name: string, parentId: number | null = null) {
    const code = resolvedCode()
    if (!code) return false
    try {
      const { data } = await createLocatorDirectory({
        project_code: code,
        name: name.trim(),
        parent_id: parentId,
      })
      if (data.status) {
        ElMessage.success('目录已创建')
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '创建目录失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '创建目录失败'))
      return false
    }
  }

  async function renameDirectory(dirId: number, name: string) {
    try {
      const { data } = await updateLocatorDirectory(dirId, { name: name.trim() })
      if (data.status) {
        ElMessage.success('目录已更新')
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '更新失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '更新失败'))
      return false
    }
  }

  async function removeDirectory(dirId: number) {
    try {
      const { data } = await deleteLocatorDirectory(dirId)
      if (data.status) {
        ElMessage.success('目录已删除')
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '删除失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '删除失败'))
      return false
    }
  }

  async function addFile(name: string, directoryId: number | null = null) {
    const code = resolvedCode()
    if (!code) return null
    const trimmed = name.trim()
    try {
      let payload: Record<string, unknown>
      if (code === 'android') {
        const { data } = await apiCreatePage({ label: trimmed, directory_id: directoryId })
        payload = data as Record<string, unknown>
      } else if (code === 'web') {
        const { data } = await apiCreateWebElement({
          name: trimmed,
          locator_type: 'css_selector',
          locator_value: 'body',
          directory_id: directoryId,
        })
        payload = data as Record<string, unknown>
      } else {
        const { data } = await apiCreateApiEndpoint({
          name: trimmed,
          method: 'GET',
          url: '/',
          directory_id: directoryId,
        })
        payload = data as Record<string, unknown>
      }
      if (payload.status) {
        ElMessage.success('文件已创建')
        await loadTree()
        return createdLeafId(payload)
      }
      ElMessage.error((payload.message as string) || '创建文件失败')
      return null
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '创建文件失败'))
      return null
    }
  }

  async function removeFile(fileId: number, kind?: LocatorFileKind) {
    const resolvedKind = kind || (resolvedCode() ? FILE_KIND_BY_CODE[resolvedCode() as LocatorProjectCode] : null)
    if (!resolvedKind) return false
    try {
      let ok = false
      if (resolvedKind === 'page') {
        const { data } = await apiDeletePage(fileId)
        ok = Boolean((data as { status?: boolean }).status)
      } else if (resolvedKind === 'web_element') {
        const { data } = await apiDeleteWebElement(fileId)
        ok = Boolean((data as { status?: boolean }).status)
      } else {
        const { data } = await apiDeleteApiEndpoint(fileId)
        ok = Boolean((data as { status?: boolean }).status)
      }
      if (ok) {
        ElMessage.success('文件已删除')
        await loadTree()
        return true
      }
      ElMessage.error('删除失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '删除失败'))
      return false
    }
  }

  async function removeFiles(ids: number[]) {
    const code = resolvedCode()
    if (!code || !ids.length) return false
    try {
      const { data } = await batchDeleteLocatorFiles({
        kind: FILE_KIND_BY_CODE[code],
        ids,
      })
      if (data.status) {
        ElMessage.success('已删除选中文件')
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '批量删除失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '批量删除失败'))
      return false
    }
  }

  async function moveTreeItem(
    kind: 'directory' | LocatorFileKind,
    itemId: number,
    parentDirectoryId: number | null,
  ) {
    try {
      const { data } = await moveLocatorItem({
        kind,
        id: itemId,
        parent_directory_id: parentDirectoryId,
      })
      if (data.status) {
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '移动失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '移动失败'))
      return false
    }
  }

  return {
    project,
    tree,
    loading,
    error,
    loadTree,
    addDirectory,
    renameDirectory,
    removeDirectory,
    addFile,
    removeFile,
    removeFiles,
    moveTreeItem,
  }
}
