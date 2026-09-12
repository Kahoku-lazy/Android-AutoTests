<script setup lang="ts">
/**
 * ProjectTree — Doodle Craft 资源管理器（方案 A）
 * 全宽卡片行：目录展开 / 点文件进表格；保留右键、拖拽、多选。
 */
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import type { TreeNode } from '../types'

interface UiTreeNode {
  key: string
  type: 'directory' | 'file'
  id: number
  name: string
  sort_order: number
  updated_at?: string
  children?: UiTreeNode[]
}

const props = defineProps<{
  treeData: TreeNode[]
  activeFileId: number | null
}>()

const emit = defineEmits<{
  selectFile: [fileId: number]
  refresh: []
  createDirectory: [payload: { name: string; parentId: number | null }]
  renameDirectory: [payload: { id: number; name: string }]
  deleteDirectory: [id: number]
  createFile: [payload: { name: string; directoryId: number | null }]
  renameFile: [payload: { id: number; name: string }]
  deleteFile: [fileId: number]
  moveItem: [payload: {
    itemType: 'directory' | 'file'
    itemId: number
    targetDirectoryId: number | null
  }]
}>()

const treeRef = ref<{
  getCheckedKeys: () => Array<string | number>
  setCheckedKeys: (keys: Array<string | number>) => void
  getNode: (key: string) => { expanded?: boolean } | null
} | null>(null)

function toUiNodes(nodes: TreeNode[]): UiTreeNode[] {
  return nodes.map((node) => {
    if (node.type === 'directory') {
      return {
        key: `d-${node.id}`,
        type: 'directory',
        id: node.id,
        name: node.name,
        sort_order: node.sort_order,
        children: toUiNodes(node.children || []),
      }
    }
    return {
      key: `f-${node.id}`,
      type: 'file',
      id: node.id,
      name: node.name,
      sort_order: node.sort_order,
      updated_at: node.updated_at,
    }
  })
}

function collectFileKeys(nodes: UiTreeNode[], result: string[] = []): string[] {
  for (const node of nodes) {
    if (node.type === 'file') result.push(node.key)
    if (node.type === 'directory' && node.children?.length) collectFileKeys(node.children, result)
  }
  return result
}

function findUiByKey(nodes: UiTreeNode[], key: string): UiTreeNode | null {
  for (const node of nodes) {
    if (node.key === key) return node
    if (node.children?.length) {
      const found = findUiByKey(node.children, key)
      if (found) return found
    }
  }
  return null
}

function childCount(data: UiTreeNode): number {
  return data.children?.length ?? 0
}

function formatTime(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16).replace('T', ' ')
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const elTreeData = computed(() => toUiNodes(props.treeData))
const allFileKeys = computed(() => collectFileKeys(elTreeData.value))
const activeKey = computed(() => (props.activeFileId != null ? `f-${props.activeFileId}` : undefined))
const defaultExpanded = computed(() =>
  elTreeData.value.filter((n) => n.type === 'directory').map((n) => n.key),
)

// ── Select mode ──
const selectMode = ref(false)
const checkedCount = ref(0)
const selectAll = ref(false)

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  if (!selectMode.value) {
    checkedCount.value = 0
    selectAll.value = false
    treeRef.value?.setCheckedKeys([])
  }
}

function handleCheck() {
  nextTick(() => {
    const keys = (treeRef.value?.getCheckedKeys() || []).map(String)
    const fileKeys = keys.filter((k) => k.startsWith('f-'))
    checkedCount.value = fileKeys.length
    selectAll.value = fileKeys.length > 0 && fileKeys.length === allFileKeys.value.length
  })
}

function handleSelectAll() {
  if (selectAll.value) {
    treeRef.value?.setCheckedKeys([])
    selectAll.value = false
    checkedCount.value = 0
  } else {
    treeRef.value?.setCheckedKeys([...allFileKeys.value])
    selectAll.value = true
    checkedCount.value = allFileKeys.value.length
  }
}

async function confirmBatchDelete() {
  const keys = (treeRef.value?.getCheckedKeys() || []).map(String)
  const fileIds = keys
    .map((k) => findUiByKey(elTreeData.value, k))
    .filter((n): n is UiTreeNode => !!n && n.type === 'file')
    .map((n) => n.id)
  if (!fileIds.length) {
    ElMessage.warning('请勾选要删除的文件')
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${fileIds.length} 个文件？`, '批量删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  for (const id of fileIds) {
    emit('deleteFile', id)
  }
  toggleSelectMode()
}

// ── Context menu ──
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const menuNode = ref<UiTreeNode | null>(null)

function handleContextMenu(event: MouseEvent, data: UiTreeNode) {
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

onMounted(() => document.addEventListener('click', closeMenu))
onUnmounted(() => document.removeEventListener('click', closeMenu))

// ── Dialogs ──
const dialogVisible = ref(false)
const dialogKind = ref<'dir-create' | 'dir-rename' | 'file-create' | 'file-rename'>('dir-create')
const dialogName = ref('')
const dialogParentId = ref<number | null>(null)
const dialogNodeId = ref<number | null>(null)

const dialogTitle = computed(() => {
  switch (dialogKind.value) {
    case 'dir-create':
      return '新建目录'
    case 'dir-rename':
      return '重命名目录'
    case 'file-create':
      return '新建文件'
    case 'file-rename':
      return '重命名文件'
    default:
      return ''
  }
})

function openCreateRootDir() {
  dialogKind.value = 'dir-create'
  dialogName.value = ''
  dialogParentId.value = null
  dialogNodeId.value = null
  dialogVisible.value = true
}

function openCreateRootFile() {
  dialogKind.value = 'file-create'
  dialogName.value = ''
  dialogParentId.value = null
  dialogNodeId.value = null
  dialogVisible.value = true
}

function openCreateSubDir() {
  if (!menuNode.value || menuNode.value.type !== 'directory') return
  dialogKind.value = 'dir-create'
  dialogName.value = ''
  dialogParentId.value = menuNode.value.id
  dialogNodeId.value = null
  dialogVisible.value = true
  closeMenu()
}

function openCreateFile() {
  const dirId = menuNode.value?.type === 'directory' ? menuNode.value.id : null
  dialogKind.value = 'file-create'
  dialogName.value = ''
  dialogParentId.value = dirId
  dialogNodeId.value = null
  dialogVisible.value = true
  closeMenu()
}

function openRename() {
  if (!menuNode.value) return
  dialogKind.value = menuNode.value.type === 'directory' ? 'dir-rename' : 'file-rename'
  dialogName.value = menuNode.value.name
  dialogNodeId.value = menuNode.value.id
  dialogVisible.value = true
  closeMenu()
}

function confirmDialog() {
  const name = dialogName.value.trim()
  if (!name) {
    ElMessage.warning(dialogKind.value.startsWith('file') ? '请输入文件名称' : '请输入目录名称')
    return
  }
  if (dialogKind.value === 'dir-create') {
    emit('createDirectory', { name, parentId: dialogParentId.value })
  } else if (dialogKind.value === 'dir-rename' && dialogNodeId.value != null) {
    emit('renameDirectory', { id: dialogNodeId.value, name })
  } else if (dialogKind.value === 'file-create') {
    emit('createFile', { name, directoryId: dialogParentId.value })
  } else if (dialogKind.value === 'file-rename' && dialogNodeId.value != null) {
    emit('renameFile', { id: dialogNodeId.value, name })
  }
  dialogVisible.value = false
}

async function onDeleteDirectory() {
  if (!menuNode.value || menuNode.value.type !== 'directory') return
  const id = menuNode.value.id
  closeMenu()
  try {
    await ElMessageBox.confirm('删除目录将同时删除其下全部子目录与文件，是否继续？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  emit('deleteDirectory', id)
}

async function onDeleteFile() {
  if (!menuNode.value || menuNode.value.type !== 'file') return
  const fileId = menuNode.value.id
  const name = menuNode.value.name
  closeMenu()
  try {
    await ElMessageBox.confirm(`确认删除文件「${name}」及其全部用例行？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  emit('deleteFile', fileId)
}

function handleNodeClick(data: UiTreeNode) {
  if (selectMode.value) return
  if (data.type === 'file') emit('selectFile', data.id)
}

function allowDrag(node: { data?: UiTreeNode }) {
  return !selectMode.value && !!node?.data
}

function allowDrop(
  _draggingNode: unknown,
  dropNode: { data?: UiTreeNode },
  type: string,
) {
  const target = dropNode?.data
  if (!target) return false
  if (type === 'inner' && target.type !== 'directory') return false
  return true
}

async function handleNodeDrop(
  draggingNode: { data?: UiTreeNode },
  dropNode: { data?: UiTreeNode },
  dropType: 'before' | 'after' | 'inner',
) {
  const source = draggingNode?.data
  const dropData = dropNode?.data
  if (!source || !dropData) return
  let targetDirectoryId: number | null = null
  if (dropType === 'inner' && dropData.type === 'directory') {
    targetDirectoryId = dropData.id
  } else if (dropData.type === 'directory') {
    targetDirectoryId = dropData.id
  } else {
    ElMessage.warning('请拖拽到目录节点内')
    return
  }

  const typeLabel = source.type === 'file' ? '文件' : '目录'
  try {
    await ElMessageBox.confirm(`将${typeLabel}「${source.name}」移动到目标位置？`, '确认移动', {
      confirmButtonText: '确认移动',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  emit('moveItem', {
    itemType: source.type,
    itemId: source.id,
    targetDirectoryId,
  })
}

function rowClass(data: UiTreeNode) {
  return {
    'explorer-row': true,
    'explorer-row--dir': data.type === 'directory',
    'explorer-row--file': data.type === 'file',
    'explorer-row--active': data.type === 'file' && data.id === props.activeFileId,
  }
}
</script>

<template>
  <div class="project-tree">
    <div v-if="!selectMode" class="explorer-toolbar">
      <div class="explorer-crumbs">
        <span class="explorer-crumbs__root">项目根</span>
        <span class="explorer-crumbs__sep">/</span>
        <span>全部</span>
      </div>
      <div class="explorer-toolbar__actions">
        <button type="button" class="ex-btn" @click="openCreateRootDir">+ 新建目录</button>
        <button type="button" class="ex-btn ex-btn--primary" @click="openCreateRootFile">+ 新建文件</button>
        <button type="button" class="ex-btn" @click="toggleSelectMode">选择</button>
      </div>
    </div>
    <div v-else class="explorer-toolbar explorer-toolbar--select">
      <div class="explorer-crumbs">已选 {{ checkedCount }} 个文件</div>
      <div class="explorer-toolbar__actions">
        <button type="button" class="ex-btn" @click="handleSelectAll">
          {{ selectAll ? '取消全选' : '全选' }}
        </button>
        <button
          type="button"
          class="ex-btn ex-btn--danger"
          :disabled="checkedCount === 0"
          @click="confirmBatchDelete"
        >
          删除
        </button>
        <button type="button" class="ex-btn" @click="toggleSelectMode">退出</button>
      </div>
    </div>

    <div class="explorer-body">
      <EmptyState
        v-if="!treeData.length"
        icon="📁"
        text="暂无目录或文件"
        hint="点击「新建目录」或「新建文件」开始组织用例表"
      />

      <el-tree
        v-else
        ref="treeRef"
        class="explorer-tree"
        :data="elTreeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="key"
        :indent="18"
        :default-expanded-keys="defaultExpanded"
        :expand-on-click-node="true"
        :highlight-current="!selectMode"
        :current-node-key="activeKey"
        :show-checkbox="selectMode"
        :check-strictly="false"
        :draggable="!selectMode"
        :allow-drag="allowDrag"
        :allow-drop="allowDrop"
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
        @node-drop="handleNodeDrop"
        @check="handleCheck"
      >
        <template #default="{ data, node }">
          <div :class="rowClass(data)">
            <span class="explorer-row__ico" aria-hidden="true">
              {{ data.type === 'file' ? '📄' : node.expanded ? '📂' : '📁' }}
            </span>
            <span class="explorer-row__name" :title="data.name">{{ data.name }}</span>
            <span
              class="explorer-row__kind"
              :class="data.type === 'directory' ? 'explorer-row__kind--dir' : 'explorer-row__kind--file'"
            >
              {{ data.type === 'directory' ? '目录' : '文件' }}
            </span>
            <span class="explorer-row__meta">
              {{
                data.type === 'directory'
                  ? `${childCount(data)} 项`
                  : formatTime(data.updated_at)
              }}
            </span>
            <span class="explorer-row__hint">
              {{ data.type === 'directory' ? '展开 / 收起' : '进入表格 →' }}
            </span>
          </div>
        </template>
      </el-tree>
    </div>

    <div
      v-if="menuVisible"
      class="context-menu"
      :style="{ left: menuX + 'px', top: menuY + 'px' }"
      @click.stop
    >
      <template v-if="!menuNode || menuNode.type === 'directory'">
        <div v-if="menuNode?.type === 'directory'" class="context-menu__item" @click="openCreateSubDir">
          + 新建子目录
        </div>
        <div class="context-menu__item" @click="openCreateFile">+ 新建文件</div>
        <div v-if="menuNode?.type === 'directory'" class="context-menu__item" @click="openRename">
          重命名
        </div>
        <div v-if="menuNode?.type === 'directory'" class="context-menu__divider" />
        <div
          v-if="menuNode?.type === 'directory'"
          class="context-menu__item context-menu__item--danger"
          @click="onDeleteDirectory"
        >
          删除目录
        </div>
      </template>
      <template v-else>
        <div class="context-menu__item" @click="openRename">重命名</div>
        <div class="context-menu__item context-menu__item--danger" @click="onDeleteFile">删除文件</div>
      </template>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="dialogName"
        maxlength="200"
        :placeholder="dialogKind.startsWith('file') ? '输入文件名称' : '输入目录名称'"
        @keyup.enter="confirmDialog"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDialog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.project-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.explorer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  padding: 10px 14px;
  border-bottom: 2px solid var(--case-border-subtle);
  background: color-mix(in srgb, #fff 70%, transparent);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.explorer-toolbar--select {
  background: color-mix(in srgb, var(--c-case) 12%, white);
}
.explorer-crumbs {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.explorer-crumbs__root {
  color: var(--ink);
}
.explorer-crumbs__sep {
  color: var(--app-text-secondary);
  font-weight: 500;
}
.explorer-toolbar__actions {
  display: flex;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}

.ex-btn {
  border: 2px solid var(--ink);
  background: #fff;
  border-radius: 10px;
  padding: 7px 12px;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
  color: var(--ink);
  line-height: 1.2;
}
.ex-btn:hover:not(:disabled) {
  background: var(--app-highlight, #ffe066);
}
.ex-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.ex-btn--primary {
  background: var(--c-case);
}
.ex-btn--danger {
  color: #e85d5d;
}

.explorer-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 14px 20px;
}

.explorer-tree {
  background: transparent;
  --el-tree-node-hover-bg-color: transparent;
}
.explorer-tree :deep(.el-tree-node__content) {
  height: auto;
  min-height: 0;
  padding: 0 0 var(--app-space-sm);
  background: transparent !important;
}
.explorer-tree :deep(.el-tree-node__expand-icon) {
  display: none;
}
.explorer-tree :deep(.el-tree-node__content > .el-tree-node__expand-icon) {
  display: none;
}
.explorer-tree :deep(.el-checkbox) {
  margin-right: var(--app-space-sm);
  margin-left: var(--app-space-xs);
}
.explorer-tree :deep(.el-tree-node__children) {
  padding-left: 0;
}

.explorer-row {
  display: grid;
  grid-template-columns: 28px minmax(120px, 1fr) 72px 140px 100px;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  border: 2px solid var(--ink);
  background: #fff;
  border-radius: 14px;
  padding: var(--app-space-sm) 12px;
  min-height: 44px;
}
.explorer-row--dir {
  background: #fffdf6;
}
.explorer-row--file:hover {
  background: #f3fffd;
}
.explorer-row--dir:hover {
  background: #fff8db;
}
.explorer-row--active {
  box-shadow: 3px 3px 0 var(--ink);
  background: #f3fffd;
}
.explorer-row__ico {
  font-size: 18px;
  text-align: center;
  line-height: 1;
}
.explorer-row__name {
  font-weight: 700;
  font-size: 14px;
  color: var(--ink);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.explorer-row__kind {
  font-size: var(--app-size-xs);
  font-weight: 800;
  text-align: center;
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 2px var(--app-space-sm);
  line-height: 1.3;
}
.explorer-row__kind--dir {
  background: #fff8db;
}
.explorer-row__kind--file {
  background: #e6faf8;
}
.explorer-row__meta,
.explorer-row__hint {
  font-size: 12px;
  color: var(--app-text-secondary);
  white-space: nowrap;
}
.explorer-row__hint {
  text-align: right;
  font-weight: 600;
}
.explorer-row--file .explorer-row__hint {
  color: #1a7a74;
}

.context-menu {
  position: fixed;
  z-index: var(--case-z-context);
  background: #fff;
  border: 2px solid var(--ink);
  border-radius: 14px;
  padding: 6px 0;
  min-width: 168px;
  box-shadow: 4px 4px 0 rgba(30, 30, 36, 0.15);
}
.context-menu__item {
  padding: var(--app-space-sm) var(--app-space-md);
  font-size: var(--app-size-sm);
  cursor: pointer;
}
.context-menu__item:hover {
  background: #e6faf8;
  color: #1a7a74;
}
.context-menu__item--danger:hover {
  background: #ffe8e8;
  color: #e85d5d;
}
.context-menu__divider {
  height: 1px;
  background: var(--case-border);
  margin: var(--app-space-xs) var(--app-space-sm);
}

@media (max-width: 900px) {
  .explorer-row {
    grid-template-columns: 28px minmax(80px, 1fr) 64px;
  }
  .explorer-row__meta,
  .explorer-row__hint {
    display: none;
  }
}
</style>
