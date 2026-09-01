/** useToolbox — 共享工具箱的 HTTP 编排（ToolboxPanel 只渲染，不碰网） */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchSharedTools, createSharedTool, updateSharedTool, deleteSharedTool,
  uploadSharedSkill, toggleSharedTool,
} from '../api/toolbox'

export function useToolbox() {
  const items = ref([])
  const loading = ref(false)
  const activeFilter = ref('all')
  const filters = [
    { key: 'all', label: '全部' },
    { key: 'mcp', label: 'MCP 工具' },
    { key: 'skill', label: 'Skill' },
    { key: 'extension', label: '扩展' },
  ]

  const filteredItems = computed(() => {
    if (activeFilter.value === 'all') return items.value
    return items.value.filter((i) => i.item_type === activeFilter.value)
  })

  function typeLabel(t) {
    return { mcp: 'MCP', skill: 'Skill', extension: '扩展' }[t] || t
  }

  function formatConfig(raw) {
    try { return JSON.stringify(JSON.parse(raw), null, 2) } catch { return raw }
  }

  async function loadItems() {
    loading.value = true
    try {
      const data = await fetchSharedTools()
      if (data.status) items.value = data.data?.items || []
    } catch (e) { console.error('Failed to load toolbox:', e) }
    loading.value = false
  }

  // ── MCP / Extension dialog ──
  const dialogVisible = ref(false)
  const editingId = ref(null)
  const saving = ref(false)
  const form = ref({ name: '', item_type: 'mcp', description: '', config_json: '{}' })

  function openMcpDialog() {
    editingId.value = null
    form.value = { name: '', item_type: 'mcp', description: '', config_json: '{}' }
    dialogVisible.value = true
  }

  function editItem(item) {
    editingId.value = item.id
    form.value = {
      name: item.name,
      item_type: item.item_type,
      description: item.description,
      config_json: formatConfig(item.config_json),
    }
    dialogVisible.value = true
  }

  async function saveItem() {
    if (!form.value.name.trim()) {
      ElMessage.warning('请输入名称'); return
    }
    saving.value = true
    try {
      if (editingId.value) {
        await updateSharedTool(editingId.value, { ...form.value })
        ElMessage.success('已更新')
      } else {
        await createSharedTool({ ...form.value })
        ElMessage.success('已创建')
      }
      dialogVisible.value = false
      await loadItems()
    } catch (e) { ElMessage.error('操作失败') }
    saving.value = false
  }

  async function removeItem(item) {
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

  // ── Skill folder upload ──
  async function onSkillFolderPicked(e) {
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
    e.target.value = ''
  }

  // ── 启停共享项（直接决定平台唯一智能体是否使用） ──
  const togglingId = ref<number | null>(null)
  async function toggleItem(item): Promise<void> {
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
    items, loading, activeFilter, filters, filteredItems, typeLabel, formatConfig, loadItems,
    dialogVisible, editingId, saving, form, openMcpDialog, editItem, saveItem, removeItem, onSkillFolderPicked,
    togglingId, toggleItem,
  }
}
