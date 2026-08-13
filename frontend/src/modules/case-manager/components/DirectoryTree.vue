<script setup>
/**
 * DirectoryTree — 用例目录树（选择 / 右键菜单 / 拖拽 / 批量移动）
 *
 * composable 返回值在顶层解构，模板自动 unwrap ref，避免 batch.xxx.value 嵌套写法。
 */
import { ref, computed } from "vue";
import EmptyState from "@/shared/components/patterns/EmptyState.vue";
import { useBatchSelect } from "../composables/useBatchSelect";
import { useContextMenu } from "../composables/useContextMenu";
import { useTreeDragDrop } from "../composables/useTreeDragDrop";
import { useDirectoryDialog } from "../composables/useDirectoryDialog";

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeId: { type: [Number, String], default: null },
  caseType: { type: String, default: "ui_automation" },
});

const emit = defineEmits(["select", "refresh"]);
const treeRef = ref(null);

// ── Flatten tree helpers ──
function collectNodes(nodes, result = []) {
  for (const node of nodes) {
    if (node.node_type !== "case" || node.enabled !== false) result.push(node);
    if (node.children?.length) collectNodes(node.children, result);
  }
  return result;
}

const allCheckableIds = computed(() => collectNodes([...props.treeData]).map((n) => String(n.id)));

function findNodeById(nodes, id) {
  for (const node of nodes) {
    if (String(node.id) === String(id)) return node;
    if (node.children) {
      const found = findNodeById(node.children, id);
      if (found) return found;
    }
  }
  return null;
}

// ── Directory list for batch move picker ──
const dirList = computed(() => {
  const result = [];
  function walk(nodes) {
    for (const node of nodes) {
      if (node.node_type !== "case") {
        result.push({ id: node.id, name: node.name, parent_id: node.parent_id });
      }
      if (node.children) walk(node.children);
    }
  }
  walk(props.treeData);
  return result;
});

// ── Composables（顶层解构 → 模板自动 unwrap）──
const {
  selectMode,
  selectAll,
  moveDialogVisible,
  moveTargetDirId,
  checkedCount,
  toggleSelectMode,
  handleCheck,
  handleSelectAll,
  openBatchMoveDialog,
  confirmBatchMove,
} = useBatchSelect(computed(() => props.treeData), treeRef, allCheckableIds, findNodeById, emit);

const {
  menuVisible,
  menuX,
  menuY,
  menuNode,
  handleContextMenu,
  openCreateSub,
  openRename,
  goCreateCase,
  goEditCase,
  handleDelete,
  handleDeleteCase,
} = useContextMenu(computed(() => props.caseType), emit);

const {
  dragEnabled,
  onNodeMouseDown,
  onNodeMouseUp,
  onNodeMouseLeave,
  allowDrag,
  allowDrop,
  handleNodeDrop,
} = useTreeDragDrop(emit);

const {
  dialogVisible,
  dialogMode,
  dialogName,
  openCreateRoot,
  applyCreateSub,
  applyRename,
  handleDialogConfirm,
} = useDirectoryDialog(computed(() => props.caseType), emit);

// ── Bridge context menu → dialog ──
function onCtxCreateSub() {
  applyCreateSub(openCreateSub());
}
function onCtxRename() {
  applyRename(openRename());
}
function onCtxDelete() { handleDelete(); }
function onCtxDeleteCase() { handleDeleteCase(); }
function onCtxGoCreateCase() { goCreateCase(); }
function onCtxGoEditCase() { goEditCase(); }

// ── Tree node click (ignore in select mode) ──
function handleNodeClick(data) {
  if (selectMode.value) return;
  emit("select", data);
}

// ── Tree node rendering ──
function nodeClass(data) {
  return {
    "tree-node--l1": data.parent_id === null && data.node_type !== "case",
    "tree-node--l2": data.parent_id !== null && data.node_type !== "case",
    "tree-node--case": data.node_type === "case",
    "tree-node--case-disabled": data.node_type === "case" && !data.enabled,
    "tree-node--active": data.id === props.activeId,
  };
}

function nodeIcon(data) {
  if (data.node_type === "case") return "📋";
  if (data.parent_id === null) return "📁";
  return "📂";
}
</script>

<template>
  <div class="directory-tree">
    <!-- Normal header -->
    <div v-if="!selectMode" class="tree-header">
      <span class="tree-header__title">📁 目录结构</span>
      <div class="tree-header__actions">
        <el-button size="small" type="primary" @click="toggleSelectMode" title="批量选择">☑ 选择</el-button>
        <el-button size="small" @click="openCreateRoot" title="新建一级目录">+</el-button>
      </div>
    </div>

    <!-- Select mode header -->
    <div v-else class="tree-header tree-header--select">
      <span class="tree-header__title">已选 {{ checkedCount }} 项</span>
      <div class="tree-header__actions">
        <el-button size="small" @click="handleSelectAll">
          {{ selectAll ? "☐ 取消全选" : "☑ 全选" }}
        </el-button>
        <el-button size="small" type="primary" :disabled="checkedCount === 0" @click="openBatchMoveDialog">📂 移动到...</el-button>
        <el-button size="small" @click="toggleSelectMode">✕ 退出选择</el-button>
      </div>
    </div>

    <!-- el-tree -->
    <div class="tree-body" :class="{ 'drag-mode-active': dragEnabled }">
      <EmptyState v-if="treeData.length === 0" icon="📁" text="暂无目录" hint="点击上方 + 按钮创建第一个目录" />

      <el-tree
        v-else
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        :indent="12"
        :expand-on-click-node="false"
        :highlight-current="!selectMode"
        :current-node-key="activeId"
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
        <template #default="{ data }">
          <span
            class="tree-node"
            :class="nodeClass(data)"
            @mousedown="onNodeMouseDown"
            @mouseup="onNodeMouseUp"
            @mouseleave="onNodeMouseLeave"
          >
            <span class="tree-node__icon">{{ nodeIcon(data) }}</span>
            <span class="tree-node__name" :title="data.name">{{ data.name }}</span>
            <span
              v-if="data.node_type === 'case'"
              class="tree-node__priority"
              :class="'tree-node__priority--' + (data.priority || 'P1').toLowerCase()"
            >{{ data.priority }}</span>
            <span v-else-if="data.case_count > 0" class="tree-node__count">{{ data.case_count }}</span>
          </span>
        </template>
      </el-tree>
    </div>

    <!-- Context menu -->
    <div
      v-if="menuVisible"
      class="context-menu"
      :style="{ left: menuX + 'px', top: menuY + 'px' }"
      @click.stop
    >
      <template v-if="!menuNode || menuNode.node_type !== 'case'">
        <div v-if="menuNode && menuNode.parent_id === null" class="context-menu__item" role="menuitem" tabindex="0" @click="onCtxCreateSub" @keydown.enter.prevent="onCtxCreateSub" @keydown.space.prevent="onCtxCreateSub">+ 新建子目录</div>
        <div v-if="menuNode" class="context-menu__item" role="menuitem" tabindex="0" @click="onCtxGoCreateCase" @keydown.enter.prevent="onCtxGoCreateCase" @keydown.space.prevent="onCtxGoCreateCase">📋 新建用例</div>
        <div class="context-menu__item" role="menuitem" tabindex="0" @click="onCtxRename" @keydown.enter.prevent="onCtxRename" @keydown.space.prevent="onCtxRename">✏️ 重命名</div>
        <div class="context-menu__divider"></div>
        <div class="context-menu__item context-menu__item--danger" role="menuitem" tabindex="0" @click="onCtxDelete" @keydown.enter.prevent="onCtxDelete" @keydown.space.prevent="onCtxDelete">🗑️ 删除</div>
      </template>
      <template v-else>
        <div class="context-menu__item" role="menuitem" tabindex="0" @click="onCtxGoEditCase" @keydown.enter.prevent="onCtxGoEditCase" @keydown.space.prevent="onCtxGoEditCase">📝 编辑用例</div>
        <div class="context-menu__divider"></div>
        <div class="context-menu__item context-menu__item--danger" role="menuitem" tabindex="0" @click="onCtxDeleteCase" @keydown.enter.prevent="onCtxDeleteCase" @keydown.space.prevent="onCtxDeleteCase">🗑️ 删除用例</div>
      </template>
    </div>

    <!-- Create / Rename dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建目录' : '重命名目录'"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="dialogName"
        :placeholder="dialogMode === 'create' ? '输入目录名称，如：开关功能' : '输入新名称'"
        maxlength="200"
        @keyup.enter="handleDialogConfirm"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDialogConfirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch move target picker -->
    <el-dialog v-model="moveDialogVisible" title="选择目标目录" width="420px" :close-on-click-modal="false">
      <el-select v-model="moveTargetDirId" placeholder="选择要移动到的目录" style="width: 100%">
        <el-option v-for="dir in dirList" :key="dir.id" :label="(dir.parent_id ? '  📂 ' : '📁 ') + dir.name" :value="dir.id" />
      </el-select>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!moveTargetDirId" @click="confirmBatchMove">确认移动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.directory-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  padding: 12px 10px;
  border-bottom: 2px solid var(--case-border-subtle);
  flex-shrink: 0;
}
.tree-header--select {
  background: var(--case-bg-code);
}
.tree-header__title {
  font-weight: 700;
  font-size: var(--app-size-sm);
  color: var(--ink);
  letter-spacing: 0.02em;
  white-space: nowrap;
  flex-shrink: 0;
}
.tree-header__actions {
  display: flex;
  gap: var(--app-space-xs);
  flex-wrap: wrap;
  justify-content: flex-end;
}
.tree-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px 4px 8px;
}
.tree-body :deep(.el-tree) { background: transparent; }
.tree-body :deep(.el-tree-node__content) {
  height: auto;
  min-height: 32px;
  border-radius: var(--app-radius-md);
  padding: 3px 6px 3px 2px;
  transition: background var(--app-duration) var(--app-ease);
}
.tree-body :deep(.el-tree-node__expand-icon) { padding: var(--app-space-xs); font-size: var(--app-size-sm); }
.tree-body :deep(.el-tree-node__content:hover) { background: var(--case-bg-dragover); }
.tree-body :deep(.el-tree-node.is-current > .el-tree-node__content) { background: var(--case-bg-dragover); }
.tree-body.drag-mode-active :deep(.el-tree-node__content) { cursor: grab; }
.tree-body.drag-mode-active :deep(.el-tree-node__content:active) { cursor: grabbing; }
.tree-body :deep(.el-tree__drop-indicator) { height: 2px; background-color: var(--c-workflow); border-radius: 1px; }
.tree-body :deep(.el-tree-node.is-drop-inner > .el-tree-node__content) { background: var(--case-bg-dragover) !important; box-shadow: inset 0 0 0 2px var(--c-workflow); }

.tree-node { display: flex; align-items: flex-start; gap: 5px; font-size: var(--app-size-sm); width: 100%; min-width: 0; user-select: none; line-height: 1.35; padding: 1px 0; }
.tree-node__icon { font-size: var(--app-size-sm); flex-shrink: 0; line-height: 1.35; margin-top: 1px; }
.tree-node__name { flex: 1; min-width: 0; color: var(--ink); font-weight: 500; }
.tree-node--l1 .tree-node__name, .tree-node--l2 .tree-node__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tree-node--case .tree-node__name { white-space: normal; word-break: break-word; overflow-wrap: anywhere; }
.tree-node__count { font-size: var(--app-size-xs); color: var(--app-text-secondary); background: var(--case-bg-dragover); padding: 0 6px; border-radius: 10px; font-weight: 600; flex-shrink: 0; line-height: 18px; margin-top: 1px; }
.tree-node--l1 .tree-node__name { font-weight: 700; color: var(--ink); }
.tree-node--case .tree-node__name { font-style: italic; font-weight: 500; color: var(--app-text-secondary); }
.tree-node--case-disabled .tree-node__name { color: var(--app-text-secondary); text-decoration: line-through; }

.tree-node__priority { font-size: var(--app-size-xs); font-weight: 700; padding: 1px 5px; border-radius: 6px; flex-shrink: 0; letter-spacing: 0.02em; line-height: 16px; margin-top: 1px; }
.tree-node__priority--p0 { background: var(--case-badge-danger-bg); color: var(--case-badge-danger-text); }
.tree-node__priority--p1 { background: var(--case-badge-warn-bg); color: var(--case-badge-warn-text); }
.tree-node__priority--p2 { background: var(--case-bg-dragover); color: var(--app-text-secondary); }

.context-menu { position: fixed; z-index: var(--case-z-context); background: var(--case-context-menu-bg); border: 1px solid var(--ink); border-radius: 14px; padding: 6px 0; min-width: 160px; box-shadow: var(--app-shadow-md); }
.context-menu__item { padding: var(--app-space-sm) var(--app-space-md); font-size: var(--app-size-sm); color: var(--ink); cursor: pointer; transition: background var(--app-duration) ease; }
.context-menu__item:hover { background: var(--case-bg-code-hover); color: var(--c-workflow); }
.context-menu__item--danger:hover { background: rgba(224, 90, 90, 0.1); color: var(--case-step-error); }
.context-menu__divider { height: 1px; background: var(--case-border); margin: var(--app-space-xs) var(--app-space-sm); }
</style>
