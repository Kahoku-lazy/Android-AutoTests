import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiGetPages, apiCreatePage, apiUpdatePage, apiDeletePage,
  apiGetPageElements, apiBatchMovePages, apiClearAll,
} from '../api.js'
import { bus } from '@/shared/event-bus.js'
/**
 * Page tree state and operations — extracted from ElementManager.vue.
 */
export function useElementTree() {
  const pages = ref([])
  const selectedPage = ref(null)
  const elements = ref([])
  const loading = ref(false)
  const maxDepth = ref(5)
  const treeRef = ref(null)
  // ── Context menu ──
  const menuVisible = ref(false)
  const menuX = ref(0)
  const menuY = ref(0)
  const menuNode = ref(null)
  // ── Dialogs ──
  const showCreatePage = ref(false)
  const createParentId = ref(null)
  const createIsFolder = ref(false)
  const newPageForm = ref({ label: '', package: '', activity: '' })
  const showRenameDialog = ref(false)
  const renameTarget = ref(null)
  const renameLabel = ref('')
  // ── Selection & Clear ──
  const selectedPageIds = reactive(new Set())
  const showClearDialog = ref(false)
  const clearSelectedOnly = ref(false)
  // ── Long-press drag ──
  const dragEnabled = ref(false)
  const longPressTimer = ref(null)
  const dragSourceNode = ref(null)
  // ── Batch select / move ──
  const selectMode = ref(false)
  const selectAll = ref(false)
  const moveDialogVisible = ref(false)
  const moveTargetDirId = ref(null)
  // ── Tree helpers ──
  function buildPageTree(flatPages) {
    const map = {}
    const roots = []
    for (const p of flatPages) {
      map[p.id] = { ...p, children: [] }
    }
    for (const p of flatPages) {
      const node = map[p.id]
      if (!node) continue
      const pid = p.parent_id || null
      if (pid && map[pid]) {
        map[pid].children.push(node)
      } else {
        roots.push(node)
      }
    }
    return roots
  }
  const pageTree = computed(() => buildPageTree(pages.value))
  function collectTreeNodes(nodes, result = []) {
    for (const n of nodes) {
      result.push(n)
      if (n.children?.length) collectTreeNodes(n.children, result)
    }
    return result
  }
  const allCheckableIds = computed(() =>
    collectTreeNodes(pageTree.value).filter((n) => !n.is_folder).map((n) => n.id),
  )

  // O(1) page lookup via id → page Map
  const pageMap = computed(() => {
    const m = new Map()
    for (const p of pages.value) m.set(p.id, p)
    return m
  })

  const checkedCount = computed(() => selectedPageIds.size)

  const folderList = computed(() => {
    const result = [{ id: '__root__', label: '根目录（顶层）' }]
    for (const p of pages.value) {
      if (p.is_folder) result.push({ id: p.id, label: p.label })
    }
    return result
  })

  function findNodeById(nodes, id) {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const found = findNodeById(n.children, id)
        if (found) return found
      }
    }
    return null
  }

  function isDescendantOf(ancestorId, nodeId) {
    let current = findNodeById(pageTree.value, nodeId)
    while (current) {
      const pid = current.parent_id || null
      if (pid === ancestorId) return true
      current = pid ? findNodeById(pageTree.value, pid) : null
    }
    return false
  }

  function getPageDepth(pageId) {
    let depth = 0
    let current = findNodeById(pageTree.value, pageId)
    while (current) {
      const pid = current.parent_id || null
      if (!pid) break
      current = findNodeById(pageTree.value, pid)
      depth++
    }
    return depth
  }

  function canCreateSubFolder(parentId) {
    if (!parentId) return true
    return getPageDepth(parentId) < maxDepth.value
  }

  function siblingLabelTaken(label, parentId, excludeId = null) {
    const pid = parentId || null
    return pages.value.some(
      (p) => p.label === label && (p.parent_id || null) === pid && p.id !== excludeId,
    )
  }

  function openCreatePage(parentId = null) {
    createParentId.value = parentId
    createIsFolder.value = false
    newPageForm.value = { label: '', package: '', activity: '' }
    showCreatePage.value = true
  }

  function openCreateFolder(parentId = null) {
    if (!canCreateSubFolder(parentId)) {
      ElMessage.warning(`目录最多嵌套 ${maxDepth.value} 层`)
      return
    }
    createParentId.value = parentId
    createIsFolder.value = true
    newPageForm.value = { label: '', package: '', activity: '' }
    showCreatePage.value = true
  }

  const createDialogTitle = computed(() => {
    if (createIsFolder.value) return '新建子目录'
    return createParentId.value ? '新建子页面' : '新建页面'
  })

  // ── CRUD ──

  async function loadPages() {
    loading.value = true
    try {
      const { data } = await apiGetPages()
      if (data.ok) {
        pages.value = data.pages || []
        if (data.max_depth) maxDepth.value = data.max_depth
      }
    } catch (e) { console.error(e); }
    loading.value = false
  }

  async function selectPage(page) {
    selectedPage.value = page
    elements.value = []
    if (!page) return
    try {
      const { data } = await apiGetPageElements(page.id)
      if (data.ok) {
        // Pre-parse xpath_candidates JSON once to avoid template-level JSON.parse
        elements.value = (data.elements || []).map(e => ({
          ...e,
          _xpaths: (() => {
            try { return JSON.parse(e.xpath_candidates || '[]') }
            catch { return [] }
          })(),
          _first_xpath: (() => {
            try { return (JSON.parse(e.xpath_candidates || '[]')[0] || {}).xpath || '' }
            catch { return '' }
          })(),
        }))
      }
    } catch (e) { console.error(e); }
  }

  function startEditLabel(page) {
    renameTarget.value = page
    renameLabel.value = page.label || ''
    showRenameDialog.value = true
  }

  async function doRename() {
    const page = renameTarget.value
    if (!page) return
    const label = renameLabel.value.trim()
    if (!label) { ElMessage.warning('名称不能为空'); return }
    if (siblingLabelTaken(label, page.parent_id, page.id)) {
      ElMessage.warning(`同级名称「${label}」已存在，请使用其他名称`)
      return
    }
    try {
      const { data } = await apiUpdatePage(page.id, label)
      if (data.ok) {
        // Close dialog immediately — don't wait for full page reload
        showRenameDialog.value = false
        // Update local page object immediately for instant UI feedback
        page.label = label
        if (selectedPage.value?.id === page.id) {
          selectedPage.value = { ...selectedPage.value, label }
        }
        // Background async refresh to sync server-side changes (depth, etc.)
        loadPages().then(() => {
          if (selectedPage.value?.id === page.id) {
            selectedPage.value = pages.value.find((p) => p.id === page.id) || null
          }
        })
      } else {
        ElMessage.error(data.error || '重命名失败')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.error || '重命名失败，请检查网络连接')
    }
  }

  async function doCreatePage() {
    const label = newPageForm.value.label.trim()
    if (!label) { ElMessage.warning('请输入名称'); return }
    try {
      const { data } = await apiCreatePage({
        label,
        package: newPageForm.value.package,
        activity: newPageForm.value.activity,
        parent_id: createParentId.value ?? null,
        is_folder: createIsFolder.value,
      })
      if (data.ok) {
        showCreatePage.value = false
        newPageForm.value = { label: '', package: '', activity: '' }
        // Add new page to local array immediately for instant feedback
        if (data.page) pages.value.push(data.page)
        createParentId.value = null
        createIsFolder.value = false
        // Background sync for server-side computed fields (depth, flows, etc.)
        loadPages()
      } else {
        ElMessage.error(data.error || '创建失败')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.error || '创建失败，请检查网络连接')
    }
  }

  async function deletePage(page) {
    let msg
    if (page.is_folder) {
      const children = pages.value.filter((p) => (p.parent_id || null) === page.id)
      msg = `删除目录「${page.label}」？${children.length ? `\n将同时删除其中 ${children.length} 个页面/子目录` : ''}`
    } else {
      msg = `删除页面「${page.label}」？\n将同时删除其下的所有元素。`
    }
    try {
      await ElMessageBox.confirm(msg, '确认删除', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
      })
    } catch { return }
    try {
      const { data } = await apiDeletePage(page.id)
      if (data.ok) {
        if (selectedPage.value?.id === page.id) selectedPage.value = null
        // Remove from local array immediately, background sync for consistency
        pages.value = pages.value.filter(p => p.id !== page.id)
        loadPages()
      } else {
        ElMessage.error(data.error || '删除失败')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.error || '删除失败，请检查网络连接')
    }
  }

  function openClearDialog() {
    clearSelectedOnly.value = selectedPageIds.size > 0
    showClearDialog.value = true
  }

  async function doClearPages() {
    const ids = clearSelectedOnly.value && selectedPageIds.size > 0 ? [...selectedPageIds] : null
    try {
      const { data } = await apiClearAll(ids)
      if (data.ok) {
        showClearDialog.value = false
        selectedPage.value = null
        elements.value = []
        pages.value = []
        loadPages()
      } else {
        ElMessage.error(data.error || '清空失败')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.error || '清空失败，请检查网络连接')
    }
  }

  // ── Drag & drop ──

  function resetDragState() {
    dragEnabled.value = false
    dragSourceNode.value = null
    if (longPressTimer.value) { clearTimeout(longPressTimer.value); longPressTimer.value = null }
  }

  function onNodeMouseDown(e) {
    if (selectMode.value || e.button !== 0) return
    longPressTimer.value = setTimeout(() => {
      dragEnabled.value = true
      ElMessage.info({ message: '拖动模式已激活，拖到目标目录后松开', duration: 2000 })
    }, 500)
  }

  function onNodeMouseUp() {
    if (longPressTimer.value) { clearTimeout(longPressTimer.value); longPressTimer.value = null }
  }

  function onNodeMouseLeave() {
    onNodeMouseUp()
  }

  function allowDrag() { return dragEnabled.value }

  function allowDrop(draggingNode, dropNode, type) {
    const source = draggingNode.data
    const target = dropNode.data
    if (source.id === target.id) return false
    if (isDescendantOf(source.id, target.id)) return false
    if (type === 'inner') return target.is_folder
    return true
  }

  function resolveDropParentId(target, dropType) {
    if (dropType === 'inner') return target.id
    return target.parent_id ?? null
  }

  async function executeBatchMove(pageIds, parentId) {
    try {
      const { data } = await apiBatchMovePages(pageIds, parentId)
      if (data.ok) {
        data.errors?.forEach((e) => ElMessage.error(`${e.id}: ${e.reason}`))
        if (data.moved > 0) {
          ElMessage.success(`已移动 ${data.moved} 项`)
          selectedPageIds.clear()
          selectAll.value = false
          selectMode.value = false
          // Update parent_id locally, background sync for full refresh
          for (const pid of pageIds) {
            const p = pages.value.find(x => x.id === pid)
            if (p) p.parent_id = parentId
          }
          loadPages()
        }
      } else {
        ElMessage.error(data.error || '移动失败')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.error || '移动失败，请检查网络连接')
    }
  }

  async function handleNodeDrop(draggingNode, dropNode, dropType) {
    const source = draggingNode.data
    const target = dropNode.data
    const targetParentId = resolveDropParentId(target, dropType)
    resetDragState()
    if ((source.parent_id ?? null) === (targetParentId ?? null)) {
      ElMessage.info('已在目标位置'); return
    }
    const targetLabel = dropType === 'inner'
      ? `目录「${target.label}」`
      : (targetParentId
        ? `目录「${pages.value.find((p) => p.id === targetParentId)?.label || targetParentId}」`
        : '根目录')
    try {
      await ElMessageBox.confirm(
        `将「${source.label}」移动到 ${targetLabel}？`, '确认移动',
        { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' },
      )
    } catch { return }
    await executeBatchMove([source.id], targetParentId)
  }

  // ── Batch select ──

  function toggleSelectMode() {
    selectMode.value = !selectMode.value
    if (!selectMode.value) { selectedPageIds.clear(); selectAll.value = false }
  }

  function handleSelectAll() {
    if (selectAll.value) {
      selectedPageIds.clear(); selectAll.value = false
    } else {
      const ids = allCheckableIds.value
      selectedPageIds.clear()
      for (const id of ids) selectedPageIds.add(id)
      selectAll.value = true
    }
  }

  function openBatchMoveDialog() {
    if (selectedPageIds.size === 0) { ElMessage.warning('请先勾选要移动的页面或目录'); return }
    moveTargetDirId.value = null
    moveDialogVisible.value = true
  }

  async function confirmBatchMove() {
    if (moveTargetDirId.value === null || moveTargetDirId.value === undefined) {
      ElMessage.warning('请选择目标目录'); return
    }
    const parentId = moveTargetDirId.value === '__root__' ? null : moveTargetDirId.value
    try {
      await ElMessageBox.confirm(
        `确认将 ${selectedPageIds.size} 项移动到目标位置？`, '批量移动',
        { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' },
      )
    } catch { return }
    moveDialogVisible.value = false
    await executeBatchMove([...selectedPageIds], parentId)
  }

  // ── Context menu ──

  function handleContextMenu(event, data) {
    if (selectMode.value) return
    event.preventDefault()
    menuNode.value = data
    menuX.value = event.clientX
    menuY.value = event.clientY
    menuVisible.value = true
  }

  function closeMenu() { menuVisible.value = false; menuNode.value = null }

  function onDocumentClick() { if (menuVisible.value) closeMenu() }

  // ── Tree node display ──

  function handleTreeNodeClick(data) {
    if (selectMode.value) return
    if (data.is_folder) return
    selectPage(data)
  }

  function handleTreeCheck() {
    nextTick(() => {
      if (!treeRef.value) return
      const keys = treeRef.value.getCheckedKeys()
      selectedPageIds.clear()
      for (const id of keys) selectedPageIds.add(id)
      selectAll.value = keys.length > 0 && keys.length === allCheckableIds.value.length
    })
  }

  function nodeClass(data) {
    return {
      'tree-node--folder': data.is_folder,
      'tree-node--page': !data.is_folder,
      'tree-node--active': selectedPage.value?.id === data.id,
    }
  }

  function nodeIcon(data) {
    if (!data.is_folder) return '📄'
    return data.children?.length ? '📂' : '📁'
  }

  function pageLabel(page) {
    if (!page) return ''
    const parts = []
    let current = page
    const map = pageMap.value
    while (current) {
      parts.unshift(current.label || `Page #${current.id}`)
      const pid = current.parent_id || null
      current = pid ? map.get(pid) : null
    }
    return parts.join(' / ')
  }

  // ── Lifecycle ──

  // Auto-refresh elements when saved from discovery tab
  function onElementsSaved({ pageId }) {
    if (selectedPage.value && selectedPage.value.id === pageId) {
      selectPage(selectedPage.value)
    }
  }

  onMounted(() => {
    window.addEventListener('click', onDocumentClick)
    bus.on('elements-saved', onElementsSaved)
    loadPages()
  })

  onUnmounted(() => {
    window.removeEventListener('click', onDocumentClick)
    bus.off('elements-saved', onElementsSaved)
    resetDragState()
  })

  return {
    // State
    pages, selectedPage, elements, loading, maxDepth, treeRef,
    menuVisible, menuX, menuY, menuNode,
    showCreatePage, createParentId, createIsFolder, newPageForm, createDialogTitle,
    showRenameDialog, renameTarget, renameLabel,
    selectedPageIds, showClearDialog, clearSelectedOnly,
    dragEnabled, selectMode, selectAll, moveDialogVisible, moveTargetDirId,
    // Computed
    pageTree, pageMap, allCheckableIds, checkedCount, folderList,
    // Tree ops
    canCreateSubFolder,
    openCreatePage, openCreateFolder, doCreatePage,
    startEditLabel, doRename,
    selectPage, deletePage, openClearDialog, doClearPages,
    loadPages,
    // Drag
    onNodeMouseDown, onNodeMouseUp, onNodeMouseLeave,
    allowDrag, allowDrop, handleNodeDrop,
    // Batch select
    toggleSelectMode, handleSelectAll, openBatchMoveDialog, confirmBatchMove,
    // Context menu
    handleContextMenu, closeMenu,
    // Node display
    handleTreeNodeClick, handleTreeCheck, nodeClass, nodeIcon, pageLabel,
    // Drag state
    dragSourceNode, longPressTimer,
  }
}
