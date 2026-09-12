/** useToolbox — 共享工具箱的 HTTP 编排（ToolboxPanel 只渲染，不碰网） */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchSharedTools, deleteSharedTool,
  uploadSharedSkill, toggleSharedTool,
  type SharedToolItem,
} from '../api/toolbox'

export function useToolbox() {
  const items = ref<SharedToolItem[]>([])
  const loading = ref(false)

  async function loadItems() {
    loading.value = true
    try {
      const data = await fetchSharedTools()
      if (data.status) items.value = (data.data?.items || []) as SharedToolItem[]
    } catch (e) { console.error('Failed to load toolbox:', e) }
    loading.value = false
  }

  async function removeItem(item: SharedToolItem) {
    if (item.origin === 'local') {
      ElMessage.warning('仓库内置 Skill 不能删除')
      return
    }
    try {
      await ElMessageBox.confirm(`确定要删除 "${item.name}" 吗？`, '确认删除', { type: 'warning' })
    } catch { return }
    try {
      const data = await deleteSharedTool(item.id)
      if (data.status) {
        ElMessage.success('已删除')
        items.value = items.value.filter((i) => i.id !== item.id)
      }
    } catch (e) { ElMessage.error('删除失败') }
  }

  async function onSkillFolderPicked(e: Event) {
    const files = Array.from((e.target as HTMLInputElement).files || [])
    if (!files.length) return
    const folderName = files[0].webkitRelativePath?.split('/')[0] || 'skill'
    loading.value = true
    try {
      const data = await uploadSharedSkill(files, folderName)
      if (data.status) {
        ElMessage.success('Skill 文件夹已上传')
        await loadItems()
      } else {
        ElMessage.error(data.message || '上传失败')
      }
    } catch (e) { ElMessage.error('上传失败') }
    loading.value = false
    ;(e.target as HTMLInputElement).value = ''
  }

  const togglingId = ref<number | null>(null)
  async function toggleItem(item: SharedToolItem): Promise<void> {
    if (togglingId.value === item.id) return
    const target = !item.enabled
    togglingId.value = item.id
    try {
      const data = await toggleSharedTool(item.id, target)
      if (data.status) {
        item.enabled = target
        ElMessage.success(`${item.name} 已${target ? '启用' : '停用'}`)
      } else {
        ElMessage.error(data.message || '操作失败')
      }
    } catch (e) { ElMessage.error('操作失败') }
    finally { togglingId.value = null }
  }

  onMounted(() => loadItems())

  return {
    items, loading, loadItems,
    removeItem, onSkillFolderPicked,
    togglingId, toggleItem,
  }
}
