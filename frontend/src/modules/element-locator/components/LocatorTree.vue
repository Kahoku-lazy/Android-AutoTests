<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import {
  FILE_KIND_BY_CODE,
  isLocatorProjectCode,
  type LocatorFileKind,
  type LocatorProjectCode,
  type LocatorTreeNode,
} from '../types'

interface UiTreeNode {
  key: string
  type: 'directory' | 'file'
  id: number
  name: string
  kind?: LocatorFileKind
  children?: UiTreeNode[]
}

const props = defineProps<{
  treeData: LocatorTreeNode[]
  activeFileId: number | null
  projectCode: string
}>()

const emit = defineEmits<{
  selectFile: [fileId: number]
  createDirectory: [payload: { name: string; parentId: number | null }]
  renameDirectory: [payload: { id: number; name: string }]
  deleteDirectory: [id: number]
  createFile: [payload: { name: string; directoryId: number | null }]
  deleteFile: [payload: { fileId: number; kind: LocatorFileKind }]
}>()

function toUiNodes(nodes: LocatorTreeNode[]): UiTreeNode[] {
  return nodes.map((node) => {
    if (node.type === 'directory') {
      return {
        key: `d-${node.id}`,
        type: 'directory',
        id: node.id,
        name: node.name,
        children: toUiNodes(node.children || []),
      }
    }
    return {
      key: `f-${node.id}`,
      type: 'file',
      id: node.id,
      name: node.name,
      kind: node.kind,
    }
  })
}

const elTreeData = computed(() => toUiNodes(props.treeData))
const activeKey = computed(() => (props.activeFileId != null ? `f-${props.activeFileId}` : undefined))
const defaultExpanded = computed(() =>
  elTreeData.value.filter((n) => n.type === 'directory').map((n) => n.key),
)

const resolvedCode = computed<LocatorProjectCode | null>(() =>
  isLocatorProjectCode(props.projectCode) ? props.projectCode : null,
)
const createFileLabel = computed(() => {
  const code = resolvedCode.value
  if (code === 'android') return '新建页面'
  if (code === 'web') return '新建 Web 元素'
  if (code === 'api') return '新建接口'
  return '新建文件'
})

function fileKindOf(data: UiTreeNode): LocatorFileKind {
  if (data.kind) return data.kind
  const code = resolvedCode.value
  return code ? FILE_KIND_BY_CODE[code] : 'page'
}

function childCount(data: UiTreeNode): number {
  return data.children?.length ?? 0
}

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

const dialogVisible = ref(false)
const dialogKind = ref<'dir-create' | 'dir-rename' | 'file-create'>('dir-create')
const dialogName = ref('')
const dialogParentId = ref<number | null>(null)
const dialogNodeId = ref<number | null>(null)

const dialogTitle = computed(() => {
  if (dialogKind.value === 'dir-create') return '新建目录'
  if (dialogKind.value === 'dir-rename') return '重命名目录'
  return createFileLabel.value
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
  dialogVisible.value = true
  closeMenu()
}

function openCreateFile() {
  const dirId = menuNode.value?.type === 'directory' ? menuNode.value.id : null
  dialogKind.value = 'file-create'
  dialogName.value = ''
  dialogParentId.value = dirId
  dialogVisible.value = true
  closeMenu()
}

function openRename() {
  if (!menuNode.value || menuNode.value.type !== 'directory') return
  dialogKind.value = 'dir-rename'
  dialogName.value = menuNode.value.name
  dialogNodeId.value = menuNode.value.id
  dialogVisible.value = true
  closeMenu()
}

function confirmDialog() {
  const name = dialogName.value.trim()
  if (!name) {
    ElMessage.warning(dialogKind.value === 'file-create' ? '请输入名称' : '请输入目录名称')
    return
  }
  if (dialogKind.value === 'dir-create') {
    emit('createDirectory', { name, parentId: dialogParentId.value })
  } else if (dialogKind.value === 'dir-rename' && dialogNodeId.value != null) {
    emit('renameDirectory', { id: dialogNodeId.value, name })
  } else if (dialogKind.value === 'file-create') {
    emit('createFile', { name, directoryId: dialogParentId.value })
  }
  dialogVisible.value = false
}

async function onDeleteDirectory() {
  if (!menuNode.value || menuNode.value.type !== 'directory') return
  const id = menuNode.value.id
  closeMenu()
  try {
    await ElMessageBox.confirm('删除目录将同时删除其下全部内容，是否继续？', '确认删除', {
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
  const kind = fileKindOf(menuNode.value)
  const name = menuNode.value.name
  closeMenu()
  try {
    await ElMessageBox.confirm(`确认删除「${name}」？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  emit('deleteFile', { fileId, kind })
}

function handleNodeClick(data: UiTreeNode) {
  if (data.type === 'file') emit('selectFile', data.id)
}

function rowClass(data: UiTreeNode) {
  return {
    'locator-row': true,
    'locator-row--dir': data.type === 'directory',
    'locator-row--file': data.type === 'file',
    'locator-row--active': data.type === 'file' && data.id === props.activeFileId,
  }
}
</script>

<template>
  <div class="locator-tree">
    <div class="locator-tree__toolbar">
      <button type="button" class="ex-btn" @click="openCreateRootDir">+ 目录</button>
      <button type="button" class="ex-btn ex-btn--primary" @click="openCreateRootFile">
        + {{ createFileLabel.replace('新建', '') }}
      </button>
    </div>

    <div class="locator-tree__body">
      <EmptyState
        v-if="!treeData.length"
        icon="📁"
        text="暂无目录或文件"
        hint="点击上方按钮开始组织定位资产"
      />

      <el-tree
        v-else
        class="locator-tree__el"
        :data="elTreeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="key"
        :indent="12"
        :default-expanded-keys="defaultExpanded"
        :expand-on-click-node="true"
        highlight-current
        :current-node-key="activeKey"
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
      >
        <template #default="{ data, node }">
          <div :class="rowClass(data)">
            <span class="locator-row__ico" aria-hidden="true">
              {{ data.type === 'file' ? '📄' : node.expanded ? '📂' : '📁' }}
            </span>
            <span class="locator-row__name" :title="data.name">{{ data.name }}</span>
            <span v-if="data.type === 'directory'" class="locator-row__meta">
              {{ childCount(data) }}
            </span>
            <span v-else class="locator-row__enter" aria-hidden="true">进入 ›</span>
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
      <template v-if="menuNode?.type === 'directory'">
        <div class="context-menu__item" @click="openCreateSubDir">+ 新建子目录</div>
        <div class="context-menu__item" @click="openCreateFile">+ {{ createFileLabel }}</div>
        <div class="context-menu__item" @click="openRename">重命名</div>
        <div class="context-menu__divider" />
        <div class="context-menu__item context-menu__item--danger" @click="onDeleteDirectory">
          删除目录
        </div>
      </template>
      <template v-else>
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
        :placeholder="dialogKind === 'file-create' ? '输入名称' : '输入目录名称'"
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
.locator-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.locator-tree__toolbar {
  display: flex;
  gap: var(--app-space-sm);
  padding: var(--app-space-sm) var(--app-space-md);
  border-bottom: 2px solid var(--app-border-light);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.ex-btn {
  border: 2px solid var(--ink);
  background: var(--paper);
  border-radius: var(--app-radius-sm);
  padding: 6px 12px;
  font-weight: 700;
  font-size: var(--app-size-xs);
  cursor: pointer;
  font-family: inherit;
  color: var(--ink);
  line-height: 1.2;
}
.ex-btn:hover {
  background: var(--app-highlight);
}
.ex-btn--primary {
  background: var(--c-element);
}
.locator-tree__body {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-sm);
}
.locator-tree__el {
  background: transparent;
  --el-tree-node-hover-bg-color: transparent;
}
.locator-tree__el :deep(.el-tree-node__content) {
  height: auto;
  padding: 0 0 var(--app-space-xs);
  background: transparent !important;
}
.locator-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  min-width: 0;
  border: 2px solid var(--ink);
  background: var(--paper);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-xs) var(--app-space-sm);
}
.locator-row--active {
  box-shadow: var(--app-shadow-sm);
  background: color-mix(in srgb, var(--c-element) 16%, var(--paper));
}
.locator-row__ico {
  flex-shrink: 0;
}
.locator-row__name {
  flex: 1;
  min-width: 0;
  font-weight: 700;
  font-size: var(--app-size-sm);
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.locator-row__meta {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.locator-row__enter {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--c-element);
  opacity: 0.85;
}
.locator-row--file:hover .locator-row__enter {
  opacity: 1;
}
.context-menu {
  position: fixed;
  z-index: 80;
  background: var(--paper);
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-xs) 0;
  min-width: 160px;
  box-shadow: var(--app-shadow-md);
}
.context-menu__item {
  padding: var(--app-space-sm) var(--app-space-md);
  font-size: var(--app-size-sm);
  cursor: pointer;
}
.context-menu__item:hover {
  background: color-mix(in srgb, var(--c-element) 18%, var(--paper));
}
.context-menu__item--danger:hover {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}
.context-menu__divider {
  height: 1px;
  background: var(--app-border-light);
  margin: var(--app-space-xs) var(--app-space-sm);
}
</style>
