/** useLocatorTree — 按项目 code 加载目录树并维护目录/叶子 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import {
  apiCreatePage,
  apiDeletePage,
  createLocatorDirectory,
  deleteLocatorDirectory,
  deleteLocatorItems,
  getLocatorProjectTree,
  moveLocatorItems,
  updateLocatorDirectory,
} from '../api'
import type { LocatorMoveItem } from '../api'
import {
  isLocatorProjectCode,
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
  for (const key of ['page'] as const) {
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
      const { data } = await apiCreatePage({ label: trimmed, directory_id: directoryId })
      const payload = data as Record<string, unknown>
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

  async function removeFile(fileId: number) {
    try {
      const { data } = await apiDeletePage(fileId)
      const ok = Boolean((data as { status?: boolean }).status)
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

  /** 批量删除节点（目录连同其下页面与元素一并删除）。成功后重载目录树。 */
  async function deleteItems(items: LocatorMoveItem[]): Promise<boolean> {
    if (!items.length) {
      ElMessage.warning('请先选择要删除的节点')
      return false
    }
    try {
      const { data } = await deleteLocatorItems({ items })
      if (data.status) {
        ElMessage.success(`已删除 ${data.data?.deleted ?? items.length} 项`)
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

  /** 移动节点（单件拖动 = 1 项的批量，与勾选批量走同一端点）。成功后重载目录树。 */
  async function moveItems(
    items: LocatorMoveItem[],
    parentDirectoryId: number | null,
  ): Promise<boolean> {
    if (!items.length) {
      ElMessage.warning('请先选择要移动的节点')
      return false
    }
    try {
      const { data } = await moveLocatorItems({ items, parent_directory_id: parentDirectoryId })
      if (data.status) {
        ElMessage.success(`已移动 ${data.data?.moved ?? items.length} 项`)
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
    moveItems,
    deleteItems,
  }
}
