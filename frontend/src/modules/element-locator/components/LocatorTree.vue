<script setup lang="ts">
/**
 * 元素定位目录树：新建 / 重命名 / 删除之外，还支持拖动移动与批量勾选移动。
 * 拖动与勾选的判定逻辑在 composables/useLocatorTreeMove.ts，本组件只做渲染与事件绑定。
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import type { LocatorMoveItem } from '../api'
import type { LocatorTreeNode } from '../types'
import { useLocatorTreeMove, type UiTreeNode } from '../composables/useLocatorTreeMove'
import MoveToDirectoryDialog from './MoveToDirectoryDialog.vue'

const props = defineProps<{
  treeData: LocatorTreeNode[]
  activeFileId: number | null
  moveItems: (items: LocatorMoveItem[], parentDirectoryId: number | null) => Promise<boolean>
  deleteItems: (items: LocatorMoveItem[]) => Promise<boolean>
}>()

const emit = defineEmits<{
  selectFile: [fileId: number]
  createDirectory: [payload: { name: string; parentId: number | null }]
  renameDirectory: [payload: { id: number; name: string }]
  deleteDirectory: [id: number]
  createFile: [payload: { name: string; directoryId: number | null }]
  deleteFile: [payload: { fileId: number }]
}>()

const {
  uiTree: elTreeData,
  selectMode,
  checkedCount,
  checkedItems,
  toggleSelectMode,
  onCheck,
  clearSelection,
  moveCheckedTo,
  allowDrag,
  allowDrop,
  onNodeDragStart,
  onNodeDragEnd,
  onNodeDrop,
  onRootDrop,
  touchActive,
  touchSourceKey,
  touchTargetId,
  touchOnRoot,
  onTouchStart,
  onTouchMove,
  onTouchEnd,
  onTouchCancel,
} = useLocatorTreeMove({
  treeData: () => props.treeData,
  moveItems: (items, directoryId) => props.moveItems(items, directoryId),
})

const activeKey = computed(() => (props.activeFileId != null ? `f-${props.activeFileId}` : undefined))
const defaultExpanded = computed(() =>
  elTreeData.value.filter((n) => n.type === 'directory').map((n) => n.key),
)

function childCount(data: UiTreeNode): number {
  return data.children?.length ?? 0
}

// ── 移动到…（批量勾选后选目标目录）──
const moveDialogVisible = ref(false)

async function confirmMoveTo(directoryId: number | null) {
  await moveCheckedTo(directoryId)
}

async function confirmDeleteChecked() {
  if (!checkedItems.value.length) return
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${checkedItems.value.length} 项？目录将连同其下全部页面一并删除。`,
      '确认批量删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  const ok = await props.deleteItems(checkedItems.value)
  if (ok) clearSelection()
}

// ── 右键菜单 ──
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

// ── 新建 / 重命名弹窗 ──
const dialogVisible = ref(false)
const dialogKind = ref<'dir-create' | 'dir-rename' | 'file-create'>('dir-create')
const dialogName = ref('')
const dialogParentId = ref<number | null>(null)
const dialogNodeId = ref<number | null>(null)

const dialogTitle = computed(() => {
  if (dialogKind.value === 'dir-create') return '新建目录'
  if (dialogKind.value === 'dir-rename') return '重命名目录'
  return '新建页面'
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
  emit('deleteFile', { fileId })
}

function handleNodeClick(data: UiTreeNode) {
  // 批量选择模式下点击只用于勾选，不进入页面详情
  if (selectMode.value) return
  if (data.type === 'file') emit('selectFile', data.id)
}

function rowClass(data: UiTreeNode) {
  return {
    'locator-row': true,
    'locator-row--dir': data.type === 'directory',
    'locator-row--file': data.type === 'file',
    'locator-row--active': data.type === 'file' && data.id === props.activeFileId,
    'locator-row--drop-target': data.type === 'directory' && data.id === touchTargetId.value,
    'locator-row--dragging': data.key === touchSourceKey.value,
  }
}
</script>

<template>
  <div class="locator-tree">
    <div class="locator-tree__toolbar">
      <button type="button" class="ex-btn" @click="openCreateRootDir">+ 目录</button>
      <button type="button" class="ex-btn ex-btn--primary" @click="openCreateRootFile">
        + 页面
      </button>
      <button
        type="button"
        class="ex-btn"
        :class="{ 'ex-btn--active': selectMode }"
        @click="toggleSelectMode"
      >
        {{ selectMode ? '退出批量选择' : '批量选择' }}
      </button>
      <template v-if="selectMode">
        <span class="locator-tree__count">已选 {{ checkedCount }} 项</span>
        <button type="button" class="ex-btn" :disabled="!checkedCount" @click="moveDialogVisible = true">
          移动到…
        </button>
        <button type="button" class="ex-btn ex-btn--danger" :disabled="!checkedCount" @click="confirmDeleteChecked">
          删除
        </button>
      </template>
    </div>

    <div
      class="locator-tree__body"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchCancel"
    >
      <!-- 项目根落点：桌面用原生 drop，触摸用命中测试高亮 -->
      <div
        class="locator-tree__root-drop"
        :class="{ 'locator-tree__root-drop--over': touchOnRoot }"
        data-root-drop="1"
        @dragover.prevent
        @drop.prevent="onRootDrop"
      >
        <span aria-hidden="true">🏠</span>
        <span>项目根（把节点拖到这里移出目录）</span>
      </div>

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
        :draggable="!touchActive"
        :allow-drag="allowDrag"
        :allow-drop="allowDrop"
        :show-checkbox="selectMode"
        :check-strictly="true"
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
        @node-drag-start="onNodeDragStart"
        @node-drag-end="onNodeDragEnd"
        @node-drop="onNodeDrop"
        @check="onCheck"
      >
        <template #default="{ data, node }">
          <div :class="rowClass(data)" :data-node-key="data.key" :data-node-type="data.type">
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
        <div class="context-menu__item" @click="openCreateFile">+ 新建页面</div>
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

    <MoveToDirectoryDialog
      v-model="moveDialogVisible"
      :tree-data="treeData"
      @confirm="confirmMoveTo"
    />
  </div>
</template>

<style scoped src="./LocatorTree.style.css"></style>
