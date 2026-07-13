<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { animate, stagger } from 'animejs'
import {
  apiGetPages, apiCreatePage, apiUpdatePage, apiDeletePage,
  apiGetPageElements, apiAddElementToPage, apiUpdateElement, apiClearAll,
  apiBatchMovePages,
} from '../api.js'
import { Modal, Button as AnimalButton, Card, Table, Tabs, Input, Switch } from 'animal-island-vue'

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

const showAddElement = ref(false)
const newElForm = ref({ alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false })

const showRenameDialog = ref(false)
const renameTarget = ref(null)
const renameLabel = ref('')

// ── Selection & Clear dialog ──
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

function buildPageTree(flatPages) {
  const byId = new Map()
  const roots = []
  for (const p of flatPages) {
    byId.set(p.id, { ...p, children: [] })
  }
  for (const p of flatPages) {
    const node = byId.get(p.id)
    if (p.parent_id && byId.has(p.parent_id)) {
      byId.get(p.parent_id).children.push(node)
    } else {
      roots.push(node)
    }
  }
  const sortNodes = (nodes) => {
    nodes.sort((a, b) => {
      if (a.is_folder !== b.is_folder) return a.is_folder ? -1 : 1
      return (a.label || '').localeCompare(b.label || '', 'zh-CN')
    })
    nodes.forEach((n) => sortNodes(n.children))
  }
  sortNodes(roots)
  return roots
}

const pageTree = computed(() => buildPageTree(pages.value))

function collectTreeNodes(nodes, result = []) {
  for (const node of nodes) {
    result.push(node)
    if (node.children?.length) collectTreeNodes(node.children, result)
  }
  return result
}

const allCheckableIds = computed(() =>
  collectTreeNodes(pageTree.value).map((n) => n.id),
)

const checkedCount = computed(() => selectedPageIds.size)

const folderList = computed(() => {
  const selected = new Set(selectedPageIds)
  const blocked = new Set()
  for (const id of selected) {
    const node = findNodeById(pageTree.value, id)
    if (node?.is_folder) {
      collectTreeNodes([node]).forEach((n) => blocked.add(n.id))
    }
  }
  const result = [{ id: '__root__', label: '📁 根目录（顶层）', depth: 0 }]
  const walk = (nodes, depth) => {
    for (const n of nodes) {
      if (!n.is_folder || blocked.has(n.id)) continue
      result.push({
        id: n.id,
        label: `${'  '.repeat(depth)}${depth ? '📂 ' : '📁 '}${n.label}`,
        depth,
      })
      if (n.children?.length) walk(n.children, depth + 1)
    }
  }
  walk(pageTree.value, 0)
  return result
})

function findNodeById(nodes, id) {
  for (const node of nodes) {
    if (node.id === id) return node
    if (node.children?.length) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

function isDescendantOf(ancestorId, nodeId) {
  const node = findNodeById(pageTree.value, nodeId)
  if (!node) return false
  let current = pages.value.find((p) => p.id === nodeId)
  while (current?.parent_id) {
    if (current.parent_id === ancestorId) return true
    current = pages.value.find((p) => p.id === current.parent_id)
  }
  return false
}

function getPageDepth(pageId) {
  let depth = 1
  let current = pages.value.find((p) => p.id === pageId)
  while (current?.parent_id) {
    depth += 1
    current = pages.value.find((p) => p.id === current.parent_id)
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

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  if (!selectMode.value) {
    selectedPageIds.clear()
    selectAll.value = false
    treeRef.value?.setCheckedKeys([])
  }
}

function handleSelectAll() {
  if (!treeRef.value) return
  if (selectAll.value) {
    selectedPageIds.clear()
    selectAll.value = false
    treeRef.value.setCheckedKeys([])
  } else {
    const ids = allCheckableIds.value
    selectedPageIds.clear()
    for (const id of ids) selectedPageIds.add(id)
    selectAll.value = true
    treeRef.value.setCheckedKeys(ids)
  }
}

function resetDragState() {
  dragEnabled.value = false
  dragSourceNode.value = null
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
  treeRef.value?.$el?.classList.remove('drag-mode-active')
}

function onNodeMouseDown(e, data) {
  if (selectMode.value || e.button !== 0) return
  dragSourceNode.value = data
  longPressTimer.value = setTimeout(() => {
    dragEnabled.value = true
    treeRef.value?.$el?.classList.add('drag-mode-active')
    ElMessage.info({ message: '拖动模式已激活，拖到目标目录后松开', duration: 2000 })
  }, 500)
}

function onNodeMouseUp() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
}

function onNodeMouseLeave() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
}

function allowDrag() {
  return dragEnabled.value
}

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

async function handleNodeDrop(draggingNode, dropNode, dropType) {
  const source = draggingNode.data
  const target = dropNode.data
  const targetParentId = resolveDropParentId(target, dropType)
  resetDragState()

  if ((source.parent_id ?? null) === (targetParentId ?? null)) {
    ElMessage.info('已在目标位置')
    return
  }

  const targetLabel = dropType === 'inner'
    ? `目录「${target.label}」`
    : (targetParentId
      ? `目录「${pages.value.find((p) => p.id === targetParentId)?.label || targetParentId}」`
      : '根目录')

  try {
    await ElMessageBox.confirm(
      `将「${source.label}」移动到 ${targetLabel}？`,
      '确认移动',
      { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }

  await executeBatchMove([source.id], targetParentId)
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
        treeRef.value?.setCheckedKeys([])
        await loadPages()
      }
    } else {
      ElMessage.error(data.error || '移动失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '移动失败，请检查网络连接')
  }
}

function openBatchMoveDialog() {
  if (selectedPageIds.size === 0) {
    ElMessage.warning('请先勾选要移动的页面或目录')
    return
  }
  moveTargetDirId.value = null
  moveDialogVisible.value = true
}

async function confirmBatchMove() {
  if (moveTargetDirId.value === null || moveTargetDirId.value === undefined) {
    ElMessage.warning('请选择目标目录')
    return
  }
  const parentId = moveTargetDirId.value === '__root__' ? null : moveTargetDirId.value
  const ids = [...selectedPageIds]
  try {
    await ElMessageBox.confirm(
      `确认将 ${ids.length} 项移动到目标位置？`,
      '批量移动',
      { confirmButtonText: '确认移动', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  moveDialogVisible.value = false
  await executeBatchMove(ids, parentId)
}

function handleContextMenu(event, data) {
  if (selectMode.value) return
  event.preventDefault()
  menuNode.value = data
  menuX.value = event.clientX
  menuY.value = event.clientY
  menuVisible.value = true
}

function closeMenu() {
  menuVisible.value = false
  menuNode.value = null
}

function onDocumentClick() {
  if (menuVisible.value) closeMenu()
}

onMounted(() => {
  window.addEventListener('click', onDocumentClick)
  loadPages()
})
onUnmounted(() => {
  window.removeEventListener('click', onDocumentClick)
  resetDragState()
})

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

const createDialogTitle = computed(() => {
  if (createIsFolder.value) return '新建子目录'
  return createParentId.value ? '新建子页面' : '新建页面'
})

async function loadPages() {
  loading.value = true
  try {
    const { data } = await apiGetPages()
    if (data.ok) {
      pages.value = data.pages || []
      if (data.max_depth) maxDepth.value = data.max_depth
    }
  } catch (_) { /* 加载失败时保持空列表，不打扰用户 */ }
  loading.value = false
}

async function selectPage(page) {
  selectedPage.value = page
  elements.value = []
  if (!page) return
  try {
    const { data } = await apiGetPageElements(page.id)
    if (data.ok) elements.value = data.elements || []
  } catch (_) { /* 加载元素失败时保持空列表 */ }
  await nextTick()
  animate('.elements-table tbody tr', {
    opacity: [0, 1],
    translateY: [24, 0],
    scale: [0.96, 1],
    delay: stagger(35, { from: 'center', ease: 'outExpo' }),
    duration: 400,
    easing: 'easeOutCubic',
  })
}

// ── Create page / folder ──
async function doCreatePage() {
  const label = newPageForm.value.label.trim()
  if (!label) {
    ElMessage.warning('请输入名称')
    return
  }
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
      createParentId.value = null
      createIsFolder.value = false
      await loadPages()
    } else {
      ElMessage.error(data.error || '创建失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '创建失败，请检查网络连接')
  }
}

// ── Add element ──
function openAddElement() {
  // Pre-fill info from current device
  newElForm.value = { alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false }
  showAddElement.value = true
}

async function doAddElement() {
  if (!newElForm.value.alias.trim()) {
    ElMessage.warning('请输入元素名称')
    return
  }
  try {
    const { data } = await apiAddElementToPage(selectedPage.value.id, newElForm.value)
    if (data.ok) {
      showAddElement.value = false
      await selectPage(selectedPage.value)  // refresh elements
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '添加元素失败，请检查网络连接')
  }
}

// ── Page label edit ──
function startEditLabel(page) {
  renameTarget.value = page
  renameLabel.value = page.label || ''
  showRenameDialog.value = true
}

async function doRename() {
  const page = renameTarget.value
  if (!page) return
  const label = renameLabel.value.trim()
  if (!label) {
    ElMessage.warning('名称不能为空')
    return
  }
  if (siblingLabelTaken(label, page.parent_id, page.id)) {
    ElMessage.warning(`同级名称「${label}」已存在，请使用其他名称`)
    return
  }
  try {
    const { data } = await apiUpdatePage(page.id, label)
    if (data.ok) {
      page.label = label
      if (selectedPage.value?.id === page.id) selectedPage.value.label = label
      showRenameDialog.value = false
      renameTarget.value = null
      await loadPages()
    } else {
      ElMessage.error(data.error || '重命名失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '重命名失败，请检查网络连接')
  }
}

// ── Clear dialog ──
function openClearDialog() {
  clearSelectedOnly.value = selectedPageIds.size > 0
  showClearDialog.value = true
}

async function doClearPages() {
  showClearDialog.value = false
  if (clearSelectedOnly.value && selectedPageIds.size > 0) {
    for (const id of [...selectedPageIds]) {
      await apiDeletePage(id)
    }
    selectedPageIds.clear()
  } else {
    await apiClearAll()
  }
  // 如果当前选中的页面被删了，清空右侧面板
  if (selectedPage.value && !clearSelectedOnly.value) {
    selectedPage.value = null; elements.value = []
  }
  await loadPages()
}

async function deletePage(page) {
  if (!confirm(`确定删除「${page.label || 'Page #' + page.id}」？`)) return
  await apiDeletePage(page.id)
  if (selectedPage.value?.id === page.id) { selectedPage.value = null; elements.value = [] }
  await loadPages()
}

async function updateEl(el, field, value) {
  await apiUpdateElement(el.id, { [field]: value })
  el[field] = value
}

function pageLabel(page) {
  return page.label || `Page #${page.id}`
}

// ── Filter ──
const filterMode = ref('all')
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'clickable', label: '可点击' },
  { key: 'aliased', label: '已命名' },
  { key: 'testpoint', label: '测试点' },
]
const filteredElements = computed(() => {
  switch (filterMode.value) {
    case 'clickable': return elements.value.filter(e => e.clickable)
    case 'testpoint': return elements.value.filter(e => e.is_test_point)
    case 'aliased':   return elements.value.filter(e => e.alias)
    default:          return elements.value
  }
})

// ── Table columns（百分比宽度，铺满容器）──
const columns = [
  { title: '名称', dataIndex: 'alias', key: 'alias', width: '12%' },
  { title: 'XPath', dataIndex: 'xpath', key: 'xpath', width: '28%' },
  { title: '类名', dataIndex: 'class_name', key: 'class_name', width: '15%' },
  { title: '文本', dataIndex: 'text_val', key: 'text_val', width: '12%' },
  { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', width: '18%' },
  { title: '可点击', dataIndex: 'clickable', key: 'clickable', width: '7%', align: 'center' },
  { title: '测试点', dataIndex: 'is_test_point', key: 'is_test_point', width: '8%', align: 'center' },
]
</script>

<template>
  <div class="element-manager">
    <div class="main-layout">
        <!-- Left: Page tree -->
        <aside class="page-tree-panel">
          <div v-if="!selectMode" class="tree-header">
            <span class="tree-header__title">页面目录</span>
            <div class="tree-header__actions">
              <AnimalButton size="small" type="text" title="批量选择" @click="toggleSelectMode">☑ 选择</AnimalButton>
              <AnimalButton size="small" type="text" title="新建目录" @click="openCreateFolder()">+ 目录</AnimalButton>
              <AnimalButton size="small" type="text" title="新建页面" @click="openCreatePage()">+ 页面</AnimalButton>
              <AnimalButton size="small" type="text" danger @click="openClearDialog">清空</AnimalButton>
            </div>
          </div>
          <div v-else class="tree-header tree-header--select">
            <span class="tree-header__title">已选 {{ checkedCount }} 项</span>
            <div class="tree-header__actions">
              <AnimalButton size="small" type="text" @click="handleSelectAll">
                {{ selectAll ? '☐ 取消全选' : '☑ 全选' }}
              </AnimalButton>
              <AnimalButton
                size="small"
                type="text"
                :disabled="checkedCount === 0"
                @click="openBatchMoveDialog"
              >📂 移动到...</AnimalButton>
              <AnimalButton size="small" type="text" danger :disabled="checkedCount === 0" @click="openClearDialog">
                删除选中
              </AnimalButton>
              <AnimalButton size="small" type="text" @click="toggleSelectMode">✕ 退出</AnimalButton>
            </div>
          </div>
          <div class="tree-body" :class="{ 'drag-mode-active': dragEnabled }">
            <div v-if="loading && !pages.length" class="tree-loading">加载中...</div>
            <div v-else-if="!pages.length" class="tree-empty">
              <span class="tree-empty__icon">📁</span>
              <p class="tree-empty__text">暂无页面</p>
              <p class="tree-empty__hint">点击「+ 目录」或「+ 页面」创建</p>
            </div>
            <el-tree
              v-else
              ref="treeRef"
              :data="pageTree"
              :props="{ children: 'children', label: 'label' }"
              node-key="id"
              :indent="16"
              :expand-on-click-node="true"
              :highlight-current="!selectMode"
              :current-node-key="selectedPage?.id"
              :show-checkbox="selectMode"
              :check-strictly="true"
              :draggable="!selectMode"
              :allow-drag="allowDrag"
              :allow-drop="allowDrop"
              default-expand-all
              @node-click="handleTreeNodeClick"
              @node-contextmenu="handleContextMenu"
              @check="handleTreeCheck"
              @node-drop="handleNodeDrop"
            >
              <template #default="{ data }">
                <span
                  class="tree-node"
                  :class="nodeClass(data)"
                  @mousedown="onNodeMouseDown($event, data)"
                  @mouseup="onNodeMouseUp"
                  @mouseleave="onNodeMouseLeave"
                >
                  <span class="tree-node__icon">{{ nodeIcon(data) }}</span>
                  <span class="tree-node__name" :title="data.label">{{ data.label || `Page #${data.id}` }}</span>
                  <span v-if="!data.is_folder" class="tree-node__meta">{{ data.element_count ?? 0 }} 元素</span>
                  <span v-else-if="data.children?.length" class="tree-node__meta">{{ data.children.length }} 项</span>
                </span>
              </template>
            </el-tree>
          </div>
        </aside>

        <!-- Context menu -->
        <div
          v-if="menuVisible && menuNode"
          class="context-menu"
          :style="{ left: menuX + 'px', top: menuY + 'px' }"
          @click.stop
        >
          <template v-if="menuNode.is_folder">
            <div
              v-if="canCreateSubFolder(menuNode.id)"
              class="context-menu__item"
              @click="openCreateFolder(menuNode.id); closeMenu()"
            >+ 新建子目录</div>
            <div class="context-menu__item" @click="openCreatePage(menuNode.id); closeMenu()">+ 新建页面</div>
          </template>
          <div class="context-menu__item" @click="startEditLabel(menuNode); closeMenu()">✏️ 重命名</div>
          <div class="context-menu__divider" />
          <div class="context-menu__item context-menu__item--danger" @click="deletePage(menuNode); closeMenu()">🗑️ 删除</div>
        </div>

        <!-- Right: Element table -->
        <template v-if="selectedPage">
          <div class="elements-panel">
            <div class="panel-header">
              <h3 class="panel-title">
                {{ pageLabel(selectedPage) }}
                <span class="doc-tag">Elements</span>
              </h3>
              <AnimalButton size="small" type="primary" @click="openAddElement">+ 添加元素</AnimalButton>
            </div>
            <div class="elements-subheader">
              <Tabs
                class="element-tabs"
                :items="filterTabs"
                v-model="filterMode"
                :leaf-animation="true"
                :shadow="true"
              >
                <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
                  <div class="table-area">
                    <Card color="brown" pattern="brown" class="table-card">
                      <div class="table-scroll">
                        <Table
                        :columns="columns"
                        :data-source="filteredElements"
                        row-key="id"
                        :striped="true"
                        empty-text="暂无元素"
                        class="elements-table"
                      >
                      <!-- Custom cell: alias (inline edit) -->
                      <template #cell-alias="{ record }">
                        <input
                          class="cell-input"
                          :value="record.alias"
                          placeholder="未命名"
                          @blur="(e) => updateEl(record, 'alias', e.target.value)"
                          @keyup.enter="(e) => { updateEl(record, 'alias', e.target.value); e.target.blur() }"
                        />
                      </template>

                      <!-- Custom cell: xpath -->
                      <template #cell-xpath="{ record }">
                        <span v-if="record.xpath_candidates"
                          class="cell-code"
                          :title="(JSON.parse(record.xpath_candidates)[0] || {}).xpath || ''">
                          {{ (JSON.parse(record.xpath_candidates)[0] || {}).xpath || '—' }}
                        </span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: text_val -->
                      <template #cell-text_val="{ record }">
                        <span v-if="record.text_val" class="cell-text">{{ record.text_val }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: resource_id -->
                      <template #cell-resource_id="{ record }">
                        <span v-if="record.resource_id" class="cell-code" :title="record.resource_id">{{ record.resource_id }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: clickable -->
                      <template #cell-clickable="{ value }">
                        <span :class="['clickable-badge', value ? 'clickable-yes' : 'clickable-no']">
                          {{ value ? '✓ 可点击' : '—' }}
                        </span>
                      </template>

                      <!-- Custom cell: is_test_point -->
                      <template #cell-is_test_point="{ record }">
                        <Switch
                          size="small"
                          :model-value="record.is_test_point"
                          @update:model-value="(val) => updateEl(record, 'is_test_point', val)"
                        />
                      </template>

                      <!-- Empty state -->
                      <template #empty>
                        <div class="table-empty">
                          <span>📋</span>
                          <p>暂无元素</p>
                          <AnimalButton size="small" type="primary" @click="openAddElement">添加第一个元素</AnimalButton>
                        </div>
                      </template>
                    </Table>
                      </div>
                    </Card>
                  </div>
                </template>
              </Tabs>
              <span class="element-count">共 {{ elements.length }} 个元素</span>
            </div>
          </div>
        </template>
        <Card v-else color="brown" pattern="brown" class="empty-card">
          <div class="empty-state">← 选择页面查看元素（目录仅用于分组）</div>
        </Card>
    </div>

    <!-- Batch move dialog -->
    <Modal
      v-model:open="moveDialogVisible"
      title="选择目标目录"
      width="420px"
      :typewriter="false"
      :mask-closable="false"
      @close="moveDialogVisible = false"
    >
      <el-select
        v-model="moveTargetDirId"
        placeholder="选择要移动到的目录"
        filterable
        style="width: 100%"
      >
        <el-option
          v-for="dir in folderList"
          :key="dir.id"
          :label="dir.label"
          :value="dir.id"
        />
      </el-select>
      <template #footer>
        <AnimalButton @click="moveDialogVisible = false">取消</AnimalButton>
        <AnimalButton type="primary" :disabled="!moveTargetDirId" @click="confirmBatchMove">确认移动</AnimalButton>
      </template>
    </Modal>

    <!-- Create Page Dialog -->
    <Modal
      v-model:open="showCreatePage"
      :title="createDialogTitle"
      width="360px"
      :typewriter="false"
      :mask-closable="false"
      @close="showCreatePage = false"
    >
      <div class="form-grid">
        <label class="form-label required">{{ createIsFolder ? '目录名称' : '页面名称' }}</label>
        <Input
          v-model="newPageForm.label"
          :placeholder="createIsFolder ? '如：电商模块、登录流程' : '如：登录页、首页'"
          size="middle"
          @keyup.enter="doCreatePage"
        />
      </div>
      <template #footer>
        <AnimalButton @click="showCreatePage = false">取消</AnimalButton>
        <AnimalButton type="primary" @click="doCreatePage">创建</AnimalButton>
      </template>
    </Modal>

    <!-- Rename Dialog -->
    <Modal
      v-model:open="showRenameDialog"
      :title="renameTarget?.is_folder ? '重命名目录' : '重命名页面'"
      width="360px"
      :typewriter="false"
      :mask-closable="false"
      @close="showRenameDialog = false"
    >
      <div class="form-grid">
        <label class="form-label required">名称</label>
        <Input
          v-model="renameLabel"
          placeholder="输入新名称"
          size="middle"
          @keyup.enter="doRename"
        />
      </div>
      <template #footer>
        <AnimalButton @click="showRenameDialog = false">取消</AnimalButton>
        <AnimalButton type="primary" @click="doRename">确定</AnimalButton>
      </template>
    </Modal>

    <!-- Clear Pages Confirm Dialog -->
    <Modal v-model:open="showClearDialog" title="清空页面" width="440px" :typewriter="false" :mask-closable="false">
      <div class="clear-confirm">
        <p class="clear-warning">⚠️ 此操作将永久删除页面及关联元素，不可恢复。</p>
        <p class="clear-question">
          确定要清空<strong>{{ clearSelectedOnly && selectedPageIds.size > 0 ? `选中的 ${selectedPageIds.size} 个` : '所有' }}</strong>页面吗？
        </p>
        <label class="clear-option" :class="{ disabled: selectedPageIds.size === 0 }">
          <input type="checkbox" v-model="clearSelectedOnly" :disabled="selectedPageIds.size === 0" />
          <span>仅清除选中的页面（已选 {{ selectedPageIds.size }} 个）</span>
        </label>
      </div>
      <template #footer>
        <AnimalButton @click="showClearDialog = false">取消</AnimalButton>
        <AnimalButton type="primary" danger @click="doClearPages">确定清空</AnimalButton>
      </template>
    </Modal>

    <!-- Add Element Dialog -->
    <Modal
      v-model:open="showAddElement"
      title="添加元素"
      width="500px"
      :typewriter="false"
      :mask-closable="false"
      @close="showAddElement = false"
    >
      <div class="form-grid">
        <label class="form-label required">元素名称</label>
        <Input v-model="newElForm.alias" placeholder="如：登录按钮、用户名输入框" size="middle" />
        <label class="form-label">XPath</label>
        <Input v-model="newElForm.xpath" placeholder="元素定位 XPath" size="middle" />
        <label class="form-label">类名</label>
        <Input v-model="newElForm.class_name" placeholder="android.widget.Button" size="middle" />
        <label class="form-label">文本</label>
        <Input v-model="newElForm.text_val" placeholder="元素文本内容" size="middle" />
        <label class="form-label">Resource ID</label>
        <Input v-model="newElForm.resource_id" placeholder="com.example:id/btn" size="middle" />
        <label class="form-label">可点击</label>
        <Switch v-model="newElForm.clickable" size="medium" />
      </div>
      <template #footer>
        <AnimalButton @click="showAddElement = false">取消</AnimalButton>
        <AnimalButton type="primary" @click="doAddElement">添加</AnimalButton>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.element-manager {
  flex: 1;
  min-height: 0;
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px 20px 20px;
  box-sizing: border-box;
}

.main-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
  width: 100%;
  min-height: 0;
  flex: 1;
  overflow: hidden;
  height: 100%;
}

/* ── Page tree panel ── */
.page-tree-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(139, 115, 85, 0.18);
  border-radius: 12px;
  overflow: hidden;
}

.tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.12);
  flex-shrink: 0;
  background: rgba(139, 115, 85, 0.04);
}

.tree-header--select {
  background: rgba(25, 200, 185, 0.08);
}

.tree-header__title {
  font-weight: 700;
  font-size: 13px;
  color: #6b5b48;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.tree-header__actions {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.tree-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px 4px 10px;
}

.tree-loading,
.tree-empty {
  text-align: center;
  color: var(--text-secondary, #988B7A);
  font-size: 13px;
  padding: 32px 12px;
}

.tree-empty__icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.tree-empty__text {
  margin: 0 0 4px;
  font-weight: 600;
  color: #6b5b48;
}

.tree-empty__hint {
  margin: 0;
  font-size: 12px;
}

.tree-body :deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: rgba(139, 115, 85, 0.08);
}

.tree-body :deep(.el-tree-node__content) {
  height: 32px;
  border-radius: 6px;
  margin: 1px 0;
}

.tree-body :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(25, 200, 185, 0.12);
}

/* 长按拖动模式 */
.tree-body.drag-mode-active :deep(.el-tree-node__content) {
  cursor: grab;
}

.tree-body.drag-mode-active :deep(.el-tree-node__content:active) {
  cursor: grabbing;
}

.tree-body :deep(.el-tree__drop-indicator) {
  height: 2px;
  background-color: #19c8b9;
  border-radius: 1px;
}

.tree-body :deep(.el-tree-node.is-drop-inner > .el-tree-node__content) {
  background: rgba(25, 200, 185, 0.18) !important;
  box-shadow: inset 0 0 0 2px #19c8b9;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
  padding-right: 6px;
}

.tree-node__icon {
  flex-shrink: 0;
  font-size: 14px;
  line-height: 1;
}

.tree-node__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #4a3a28;
}

.tree-node--folder .tree-node__name {
  font-weight: 600;
  color: #6b5b48;
}

.tree-node--page .tree-node__name {
  font-weight: 500;
}

.tree-node--active .tree-node__name {
  color: #0f8b7e;
  font-weight: 700;
}

.tree-node__meta {
  flex-shrink: 0;
  font-size: 11px;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.08);
  padding: 1px 6px;
  border-radius: 8px;
}

/* ── Context menu ── */
.context-menu {
  position: fixed;
  z-index: 3000;
  min-width: 148px;
  background: #fff;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(74, 58, 40, 0.12);
  padding: 4px 0;
}

.context-menu__item {
  padding: 8px 14px;
  font-size: 13px;
  color: #4a3a28;
  cursor: pointer;
  user-select: none;
}

.context-menu__item:hover {
  background: rgba(139, 115, 85, 0.08);
}

.context-menu__item--danger {
  color: #e05a5a;
}

.context-menu__divider {
  height: 1px;
  margin: 4px 8px;
  background: rgba(139, 115, 85, 0.12);
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary, #4A3A28);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(139, 115, 85, 0.1);
  color: #8b7355;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
/* ── Elements panel ── */
.elements-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  gap: 8px;
}
.elements-subheader {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex: 1;
  min-width: 0;
  min-height: 0;
  width: 100%;
  gap: 8px;
  overflow: hidden;
}
.element-tabs {
  flex: 1;
  min-width: 0;
  min-height: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.element-tabs :deep(.animal-tabs__list) {
  flex-shrink: 0;
}
.element-tabs :deep(.animal-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px 0 0;
  width: 100%;
}
.element-tabs :deep(.animal-tabs__inner) {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.element-count {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  align-self: flex-end;
  padding-top: 0;
  flex-shrink: 0;
}

/* ── Table card ── */
.table-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.table-card {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Table scroll：纵向主滚动区 + 窄屏横向滚动 */
.table-scroll {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow-y: auto;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 115, 85, 0.25) transparent;
}
.table-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.table-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.table-scroll::-webkit-scrollbar-thumb {
  background: rgba(139, 115, 85, 0.25);
  border-radius: 3px;
}
.table-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 115, 85, 0.45);
}

/* ── Elements table ── */
.elements-table {
  width: 100%;
}
.elements-table :deep(.animal-table-wrapper) {
  width: 100%;
}
.elements-table :deep(table) {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

/* ── 表头：彩色渐变 ── */
.elements-table :deep(th) {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  padding: 16px 12px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  position: sticky;
  top: 0;
  z-index: 2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.elements-table :deep(th:nth-child(1)) { background: linear-gradient(135deg, #19c8b9, #15b0a3); border-radius: 10px 0 0 0; }
.elements-table :deep(th:nth-child(2)) { background: linear-gradient(135deg, #9b8fd4, #8275c2); }
.elements-table :deep(th:nth-child(3)) { background: linear-gradient(135deg, #f0a06a, #e88d52); }
.elements-table :deep(th:nth-child(4)) { background: linear-gradient(135deg, #7db84d, #6ba33b); }
.elements-table :deep(th:nth-child(5)) { background: linear-gradient(135deg, #6c93d4, #557ec0); }
.elements-table :deep(th:nth-child(6)) { background: linear-gradient(135deg, #f0c64a, #e0b830); text-align: center; }
.elements-table :deep(th:nth-child(7)) { background: linear-gradient(135deg, #e8879b, #d47085); text-align: center; border-radius: 0 10px 0 0; }

/* ── 单元格 ── */
.elements-table :deep(td) {
  padding: 13px 12px;
  font-size: 14px;
  color: #4A3A28;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  vertical-align: middle;
  transition: all 0.2s ease;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 行交替配色（彩色） ── */
.elements-table :deep(tr:nth-child(3n+1) td) { background: rgba(25, 200, 185, 0.03); }
.elements-table :deep(tr:nth-child(3n+2) td) { background: rgba(136, 157, 240, 0.03); }
.elements-table :deep(tr:nth-child(3n) td)   { background: rgba(248, 166, 178, 0.03); }

/* ── 行 hover ── */
.elements-table :deep(tbody tr) {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.elements-table :deep(tbody tr:hover td) {
  background: rgba(139, 115, 85, 0.06) !important;
  transform: scale(1.002);
}
.elements-table :deep(tbody tr:hover) {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  z-index: 1;
  position: relative;
}

/* ── 列专属样式 ── */
/* 名称列 — 青绿色强调 */
.elements-table :deep(td:nth-child(1)) { font-weight: 600; color: #0f8b7e; font-size: 14px; }
/* XPath 列 — 紫色调，等宽字体 */
.elements-table :deep(td:nth-child(2)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #6254a0;
}
/* 类名列 — 橙色调等宽 */
.elements-table :deep(td:nth-child(3)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #b8652e;
}
/* 文本列 — 绿色调 */
.elements-table :deep(td:nth-child(4)) { color: #4a7c2e; font-size: 14px; }
/* Resource ID 列 — 蓝色调等宽 */
.elements-table :deep(td:nth-child(5)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #3b5fa0;
}
/* 可点击列 — 彩色徽章 */
.elements-table :deep(td:nth-child(6)) {
  text-align: center;
  font-size: 14px;
}
/* 测试点列 — 居中 */
.elements-table :deep(td:nth-child(7)) { text-align: center; }

/* ── 可点击徽章 ── */
.clickable-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
}
.clickable-yes {
  background: linear-gradient(135deg, #c8f0e8, #a3e8db);
  color: #0b6b5e;
}
.clickable-no {
  background: rgba(0,0,0,0.04);
  color: #bbb;
}

/* ── 空行提示 ── */
.elements-table :deep(td .text-muted) {
  color: #d0cdc8;
  font-style: italic;
  font-size: 11px;
}

/* ── Inline cell input ── */
.cell-input {
  width: 100%;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  background: transparent;
  color: #0f8b7e;
  font-weight: 600;
  outline: none;
  transition: border-color .2s;
}
.cell-input:hover { border-color: rgba(25, 200, 185, 0.25); }
.cell-input:focus { border-color: #19c8b9; background: rgba(25, 200, 185, 0.04); }

/* ── Cell code (XPath, class_name, resource_id) ── */
.cell-code {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  letter-spacing: 0.2px;
}
.cell-text {
  font-size: 14px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Empty states ── */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
  padding: 60px 0;
}
.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 0;
}
.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #988B7A;
}
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }

/* ── Utility ── */
.mono { font-family: monospace; font-size: 12px; }
.text-muted { color: #ccc; }

/* ── Modal form grid ── */
.form-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 14px 10px;
  align-items: center;
}
.form-label {
  text-align: right;
  font-size: 13px;
  color: var(--text-secondary, #988B7A);
  font-weight: 500;
  user-select: none;
}
/* ── Clear dialog ── */
.clear-confirm {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.clear-warning {
  color: #e05a5a;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  padding: 10px 14px;
  background: rgba(224, 90, 90, 0.06);
  border-radius: 10px;
  border: 1px solid rgba(224, 90, 90, 0.15);
}
.clear-question {
  font-size: 14px;
  color: var(--text-primary, #4A3A28);
  margin: 0;
}
.clear-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary, #988B7A);
  cursor: pointer;
  user-select: none;
}
.clear-option.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.clear-option input[type="checkbox"] {
  width: 16px; height: 16px;
  accent-color: var(--accent-blue, #889df0);
  cursor: pointer;
  margin: 0;
}

.form-label.required::before {
  content: '*';
  color: var(--animal-error-color, #e05a5a);
  margin-right: 3px;
}
</style>
