import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiListApiGroups, apiCreateApiGroup, apiUpdateApiGroup, apiDeleteApiGroup,
  apiListApiEndpoints, apiBatchMoveApiGroups,
} from '../api.js'

/**
 * ApiGroup tree state and operations — mirrors useWebGroupTree for el_api_groups.
 */
export function useApiGroupTree() {
  const groups = ref([])
  const selectedGroup = ref(null)
  const endpoints = ref([])
  const loading = ref(false)
  const treeRef = ref(null)

  // ── Context menu ──
  const menuVisible = ref(false)
  const menuX = ref(0)
  const menuY = ref(0)
  const menuNode = ref(null)

  // ── Dialogs ──
  const showCreateGroup = ref(false)
  const createParentId = ref(null)
  const createIsFolder = ref(false)
  const newGroupForm = ref({ name: '' })
  const showRenameDialog = ref(false)
  const renameTarget = ref(null)
  const renameLabel = ref('')

  // ── Selection & Clear ──
  const selectedGroupIds = reactive(new Set())
  const showClearDialog = ref(false)
  const clearSelectedOnly = ref(false)

  // ── Drag ──
  const dragEnabled = ref(false)
  const longPressTimer = ref(null)

  // ── Batch select / move ──
  const selectMode = ref(false)
  const moveDialogVisible = ref(false)
  const moveTargetDirId = ref(null)

  // ── Tree helpers ──
  function buildGroupTree(flatGroups) {
    const map = {}
    const roots = []
    for (const g of flatGroups) {
      map[g.id] = { ...g, children: [] }
    }
    for (const g of flatGroups) {
      const node = map[g.id]
      if (!node) continue
      const pid = g.parent_id || null
      if (pid && map[pid]) {
        map[pid].children.push(node)
      } else {
        roots.push(node)
      }
    }
    return roots
  }
  const groupTree = computed(() => buildGroupTree(groups.value))

  function collectTreeNodes(nodes, result = []) {
    for (const n of nodes) { result.push(n); if (n.children?.length) collectTreeNodes(n.children, result) }
    return result
  }

  const groupMap = computed(() => {
    const m = new Map(); groups.value.forEach(g => m.set(g.id, g)); return m
  })

  function findNodeById(nodes, id) {
    for (const n of nodes) { if (n.id === id) return n; if (n.children?.length) { const f = findNodeById(n.children, id); if (f) return f } }
    return null
  }

  function isDescendantOf(ancestorId, nodeId) {
    let cur = findNodeById(groupTree.value, nodeId)
    while (cur) { const pid = cur.parent_id || null; if (pid === ancestorId) return true; cur = pid ? findNodeById(groupTree.value, pid) : null }
    return false
  }

  const folderList = computed(() => {
    const r = [{ id: '__root__', label: '根目录（顶层）' }]
    groups.value.filter(g => g.is_folder).forEach(g => r.push({ id: g.id, label: g.name }))
    return r
  })

  // ── CRUD ──
  async function loadGroups() {
    loading.value = true
    try {
      const { data } = await apiListApiGroups()
      if (data.ok) groups.value = data.groups || []
    } catch (_) { }
    loading.value = false
  }

  async function selectGroup(groupOrNull) {
    selectedGroup.value = groupOrNull
    endpoints.value = []
    try {
      const params = groupOrNull && groupOrNull.id !== '__ungrouped__'
        ? { group_id: groupOrNull.id }
        : (groupOrNull && groupOrNull.id === '__ungrouped__' ? { group_id: 'null' } : {})
      const { data } = await apiListApiEndpoints(params)
      if (data.ok) endpoints.value = data.endpoints || []
    } catch (_) { }
  }

  function openCreateGroup(parentId = null, isFolder = false) {
    createParentId.value = parentId
    createIsFolder.value = isFolder
    newGroupForm.value = { name: '' }
    showCreateGroup.value = true
  }

  async function doCreateGroup() {
    const name = newGroupForm.value.name.trim()
    if (!name) { ElMessage.warning('请输入名称'); return }
    try {
      const { data } = await apiCreateApiGroup({
        name, parent_id: createParentId.value ?? null, is_folder: createIsFolder.value,
      })
      if (data.ok) {
        showCreateGroup.value = false
        if (data.group) groups.value.push(data.group)
        createParentId.value = null; createIsFolder.value = false
        loadGroups()
      } else { ElMessage.error(data.error || '创建失败') }
    } catch (e) { ElMessage.error('创建失败，请检查网络') }
  }

  function startEditLabel(g) {
    renameTarget.value = g; renameLabel.value = g.name || ''; showRenameDialog.value = true
  }

  async function doRename() {
    const g = renameTarget.value
    if (!g) return
    const name = renameLabel.value.trim()
    if (!name) { ElMessage.warning('名称不能为空'); return }
    try {
      const { data } = await apiUpdateApiGroup(g.id, { name })
      if (data.ok) {
        showRenameDialog.value = false; g.name = name
        if (selectedGroup.value?.id === g.id) selectedGroup.value = { ...selectedGroup.value, name }
        loadGroups()
      } else { ElMessage.error(data.error || '重命名失败') }
    } catch (e) { ElMessage.error('重命名失败，请检查网络') }
  }

  async function deleteGroup(g) {
    try {
      await ElMessageBox.confirm(
        `删除「${g.name}」？${g.is_folder ? '子分组也将被删除，接口变为未分类。' : '其中的接口将变为未分类。'}`,
        '确认删除', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
      )
    } catch { return }
    try {
      const { data } = await apiDeleteApiGroup(g.id)
      if (data.ok) {
        if (selectedGroup.value?.id === g.id) selectedGroup.value = null
        groups.value = groups.value.filter(x => x.id !== g.id)
        loadGroups()
      }
    } catch (e) { ElMessage.error('删除失败') }
  }

  // ── Drag & drop ──
  function resetDragState() { dragEnabled.value = false; if (longPressTimer.value) { clearTimeout(longPressTimer.value); longPressTimer.value = null } }
  function onNodeMouseDown(e) { if (selectMode.value || e.button !== 0) return; longPressTimer.value = setTimeout(() => { dragEnabled.value = true; ElMessage.info({ message: '拖动模式已激活', duration: 2000 }) }, 500) }
  function onNodeMouseUp() { if (longPressTimer.value) { clearTimeout(longPressTimer.value); longPressTimer.value = null } }
  function onNodeMouseLeave() { onNodeMouseUp() }
  function allowDrag() { return dragEnabled.value }
  function allowDrop(draggingNode, dropNode, type) {
    const src = draggingNode.data; const tgt = dropNode.data
    if (src.id === tgt.id || isDescendantOf(src.id, tgt.id)) return false
    if (type === 'inner') return tgt.is_folder
    return true
  }

  async function handleNodeDrop(draggingNode, dropNode, dropType) {
    const src = draggingNode.data; const tgt = dropNode.data
    const targetParentId = dropType === 'inner' ? tgt.id : (tgt.parent_id ?? null)
    resetDragState()
    if ((src.parent_id ?? null) === (targetParentId ?? null)) { ElMessage.info('已在目标位置'); return }
    try { await ElMessageBox.confirm(`将「${src.name}」移动到目标位置？`, '确认移动', { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' }) }
    catch { return }
    try {
      const { data } = await apiBatchMoveApiGroups([src.id], targetParentId)
      if (data.ok) { src.parent_id = targetParentId; loadGroups() }
    } catch (e) { ElMessage.error('移动失败') }
  }

  // ── Batch select ──
  function toggleSelectMode() { selectMode.value = !selectMode.value; if (!selectMode.value) selectedGroupIds.clear() }
  function handleSelectAll() {
    const ids = collectTreeNodes(groupTree.value).filter(n => !n.is_folder).map(n => n.id)
    if (selectedGroupIds.size === ids.length) { selectedGroupIds.clear() } else { selectedGroupIds.clear(); ids.forEach(id => selectedGroupIds.add(id)) }
  }
  function openBatchMoveDialog() {
    if (selectedGroupIds.size === 0) { ElMessage.warning('请先勾选分组'); return }
    moveTargetDirId.value = null; moveDialogVisible.value = true
  }
  async function confirmBatchMove() {
    if (!moveTargetDirId.value) { ElMessage.warning('请选择目标目录'); return }
    const pid = moveTargetDirId.value === '__root__' ? null : moveTargetDirId.value
    try { await ElMessageBox.confirm(`确认移动 ${selectedGroupIds.size} 项？`, '批量移动', { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' }) } catch { return }
    moveDialogVisible.value = false
    try {
      const { data } = await apiBatchMoveApiGroups([...selectedGroupIds], pid)
      if (data.ok) { selectedGroupIds.clear(); selectMode.value = false; loadGroups() }
    } catch (e) { ElMessage.error('移动失败') }
  }

  // ── Context menu ──
  function handleContextMenu(event, data) {
    if (selectMode.value) return
    event.preventDefault(); menuNode.value = data; menuX.value = event.clientX; menuY.value = event.clientY; menuVisible.value = true
  }
  function closeMenu() { menuVisible.value = false; menuNode.value = null }
  function onDocumentClick() { if (menuVisible.value) closeMenu() }

  // ── Node display ──
  function handleTreeNodeClick(data) {
    if (selectMode.value) return
    if (data.is_folder) return
    selectGroup(data)
  }
  function handleTreeCheck() {
    nextTick(() => { if (!treeRef.value) return; const keys = treeRef.value.getCheckedKeys(); selectedGroupIds.clear(); keys.forEach(id => selectedGroupIds.add(id)) })
  }
  function nodeClass(data) {
    return { 'tree-node--folder': data.is_folder, 'tree-node--page': !data.is_folder, 'tree-node--active': selectedGroup.value?.id === data.id }
  }
  function nodeIcon(data) { return data.is_folder ? (data.children?.length ? '📂' : '📁') : '📄' }
  function nodeName(data) { return data.name || `#${data.id}` }
  function groupLabel(g) {
    if (!g) return ''
    const parts = []; let cur = g; const map = groupMap.value
    while (cur) { parts.unshift(cur.name || `#${cur.id}`); const pid = cur.parent_id || null; cur = pid ? map.get(pid) : null }
    return parts.join(' / ')
  }

  // ── Lifecycle ──
  onMounted(() => { window.addEventListener('click', onDocumentClick); loadGroups() })
  onUnmounted(() => { window.removeEventListener('click', onDocumentClick); resetDragState() })

  return {
    groups, selectedGroup, endpoints, loading, treeRef,
    menuVisible, menuX, menuY, menuNode,
    showCreateGroup, createParentId, createIsFolder, newGroupForm,
    showRenameDialog, renameTarget, renameLabel,
    selectedGroupIds, showClearDialog, clearSelectedOnly,
    dragEnabled, selectMode, moveDialogVisible, moveTargetDirId,
    groupTree, groupMap, folderList,
    loadGroups, selectGroup,
    openCreateGroup, doCreateGroup,
    startEditLabel, doRename,
    deleteGroup,
    onNodeMouseDown, onNodeMouseUp, onNodeMouseLeave,
    allowDrag, allowDrop, handleNodeDrop,
    toggleSelectMode, handleSelectAll, openBatchMoveDialog, confirmBatchMove,
    handleContextMenu, closeMenu,
    handleTreeNodeClick, handleTreeCheck, nodeClass, nodeIcon, nodeName, groupLabel,
  }
}
