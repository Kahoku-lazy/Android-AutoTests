/** useProjectTree — 项目目录树加载与节点操作（目录 + 文件） */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import {
  createDirectory,
  createFile,
  deleteDirectory,
  deleteFile,
  getProjectTree,
  moveItem,
  updateDirectory,
  updateFile,
} from '../api'
import type { CaseProject, TreeNode } from '../types'

export function useProjectTree(projectId: () => number) {
  const project = ref<CaseProject | null>(null)
  const tree = ref<TreeNode[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadTree() {
    const id = projectId()
    if (!id) return
    loading.value = true
    error.value = null
    try {
      const { data } = await getProjectTree(id)
      if (data.status && data.data) {
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
    const id = projectId()
    try {
      const { data } = await createDirectory({
        project_id: id,
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
      const { data } = await updateDirectory(dirId, { name: name.trim() })
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
      const { data } = await deleteDirectory(dirId)
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
    const id = projectId()
    try {
      const { data } = await createFile({
        project_id: id,
        name: name.trim(),
        directory_id: directoryId,
      })
      if (data.status && data.data) {
        ElMessage.success('文件已创建')
        await loadTree()
        return data.data.id
      }
      ElMessage.error(data.message || '创建文件失败')
      return null
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '创建文件失败'))
      return null
    }
  }

  async function renameFile(fileId: number, name: string) {
    try {
      const { data } = await updateFile(fileId, { name: name.trim() })
      if (data.status) {
        ElMessage.success('文件已重命名')
        await loadTree()
        return true
      }
      ElMessage.error(data.message || '重命名失败')
      return false
    } catch (e: unknown) {
      ElMessage.error(formatApiError(e, '重命名失败'))
      return false
    }
  }

  async function removeFile(fileId: number) {
    try {
      const { data } = await deleteFile(fileId)
      if (data.status) {
        ElMessage.success('文件已删除')
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

  async function moveTreeItem(
    itemType: 'directory' | 'file',
    itemId: number | string,
    targetDirectoryId: number | null,
  ) {
    const id = projectId()
    try {
      const { data } = await moveItem({
        project_id: id,
        item_type: itemType,
        item_id: itemId,
        target_directory_id: targetDirectoryId,
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
    renameFile,
    removeFile,
    moveTreeItem,
  }
}
