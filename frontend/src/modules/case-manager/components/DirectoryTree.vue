<script setup>
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

// ── Composables ──
const batch = useBatchSelect(() => props.treeData, treeRef, allCheckableIds, findNodeById, emit);
const ctxMenu = useContextMenu(computed(() => props.caseType), emit);
const drag = useTreeDragDrop(emit);
const dirDialog = useDirectoryDialog(computed(() => props.caseType), emit);

// ── Bridge context menu → dialog ──
function onCtxCreateSub() {
  const info = ctxMenu.openCreateSub();
  dirDialog.applyCreateSub(info);
}
function onCtxRename() {
  const info = ctxMenu.openRename();
  dirDialog.applyRename(info);
}
function onCtxDelete() { ctxMenu.handleDelete(); }
function onCtxDeleteCase() { ctxMenu.handleDeleteCase(); }
function onCtxGoCreateCase() { ctxMenu.goCreateCase(); }
function onCtxGoEditCase() { ctxMenu.goEditCase(); }

// ── Tree node click (ignore in select mode) ──
function handleNodeClick(data) {
  if (batch.selectMode.value) return;
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
    <div v-if="!batch.selectMode.value" class="tree-header">
      <span class="tree-header__title">📁 目录结构</span>
      <div class="tree-header__actions">
        <el-button size="small" type="primary" @click="batch.toggleSelectMode" title="批量选择">☑ 选择</el-button>
        <el-button size="small" @click="dirDialog.openCreateRoot" title="新建一级目录">+</el-button>
      </div>
    </div>

    <!-- Select mode header -->
    <div v-else class="tree-header tree-header--select">
      <span class="tree-header__title">已选 {{ batch.checkedCount.value }} 项</span>
      <div class="tree-header__actions">
        <el-button size="small" @click="batch.handleSelectAll">
          {{ batch.selectAll.value ? "☐ 取消全选" : "☑ 全选" }}
        </el-button>
        <el-button size="small" type="primary" :disabled="batch.checkedCount.value === 0" @click="batch.openBatchMoveDialog">📂 移动到...</el-button>
        <el-button size="small" @click="batch.toggleSelectMode">✕ 退出选择</el-button>
      </div>
    </div>

    <!-- el-tree -->
    <div class="tree-body" :class="{ 'drag-mode-active': drag.dragEnabled.value }">
      <EmptyState v-if="treeData.length === 0" icon="📁" text="暂无目录" hint="点击上方 + 按钮创建第一个目录" />

      <el-tree
        v-else
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        :indent="12"
        :expand-on-click-node="false"
        :highlight-current="!batch.selectMode.value"
        :current-node-key="activeId"
        :show-checkbox="batch.selectMode.value"
        :check-strictly="false"
        :draggable="!batch.selectMode.value"
        :allow-drag="drag.allowDrag"
        :allow-drop="drag.allowDrop"
        @node-click="handleNodeClick"
        @node-contextmenu="ctxMenu.handleContextMenu"
        @node-drop="drag.handleNodeDrop"
        @check="batch.handleCheck"
      >
        <template #default="{ data }">
          <span
            class="tree-node"
            :class="nodeClass(data)"
            @mousedown="drag.onNodeMouseDown"
            @mouseup="drag.onNodeMouseUp"
            @mouseleave="drag.onNodeMouseLeave"
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
      v-if="ctxMenu.menuVisible.value"
      class="context-menu"
      :style="{ left: ctxMenu.menuX.value + 'px', top: ctxMenu.menuY.value + 'px' }"
      @click.stop
    >
      <template v-if="!ctxMenu.menuNode.value || ctxMenu.menuNode.value.node_type !== 'case'">
        <div v-if="ctxMenu.menuNode.value && ctxMenu.menuNode.value.parent_id === null" class="context-menu__item" @click="onCtxCreateSub">+ 新建子目录</div>
        <div v-if="ctxMenu.menuNode.value" class="context-menu__item" @click="onCtxGoCreateCase">📋 新建用例</div>
        <div class="context-menu__item" @click="onCtxRename">✏️ 重命名</div>
        <div class="context-menu__divider"></div>
        <div class="context-menu__item context-menu__item--danger" @click="onCtxDelete">🗑️ 删除</div>
      </template>
      <template v-else>
        <div class="context-menu__item" @click="onCtxGoEditCase">📝 编辑用例</div>
        <div class="context-menu__divider"></div>
        <div class="context-menu__item context-menu__item--danger" @click="onCtxDeleteCase">🗑️ 删除用例</div>
      </template>
    </div>

    <!-- Create / Rename dialog -->
    <el-dialog
      v-model="dirDialog.dialogVisible.value"
      :title="dirDialog.dialogMode.value === 'create' ? '新建目录' : '重命名目录'"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-input v-model="dirDialog.dialogName.value" :placeholder="dirDialog.dialogMode.value === 'create' ? '输入目录名称，如：开关功能' : '输入新名称'" maxlength="200" @keyup.enter="dirDialog.handleDialogConfirm" />
      <template #footer>
        <el-button @click="dirDialog.dialogVisible.value = false">取消</el-button>
        <el-button type="primary" @click="dirDialog.handleDialogConfirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch move target picker -->
    <el-dialog v-model="batch.moveDialogVisible.value" title="选择目标目录" width="420px" :close-on-click-modal="false">
      <el-select v-model="batch.moveTargetDirId.value" placeholder="选择要移动到的目录" style="width: 100%">
        <el-option v-for="dir in dirList" :key="dir.id" :label="(dir.parent_id ? '  📂 ' : '📁 ') + dir.name" :value="dir.id" />
      </el-select>
      <template #footer>
        <el-button @click="batch.moveDialogVisible.value = false">取消</el-button>
        <el-button type="primary" :disabled="!batch.moveTargetDirId.value" @click="batch.confirmBatchMove">确认移动</el-button>
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
  gap: 8px;
  padding: 12px 10px;
  border-bottom: 2px solid rgba(162,210,255,0.18);
  flex-shrink: 0;
}
.tree-header--select {
  background: rgba(162,210,255,0.12);
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
  gap: 4px;
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
  border-radius: 8px;
  padding: 3px 6px 3px 2px;
  transition: background 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}
.tree-body :deep(.el-tree-node__expand-icon) { padding: 4px; font-size: var(--app-size-sm); }
.tree-body :deep(.el-tree-node__content:hover) { background: rgba(162,210,255,0.14); }
.tree-body :deep(.el-tree-node.is-current > .el-tree-node__content) { background: rgba(162,210,255,0.20); }
.tree-body.drag-mode-active :deep(.el-tree-node__content) { cursor: grab; }
.tree-body.drag-mode-active :deep(.el-tree-node__content:active) { cursor: grabbing; }
.tree-body :deep(.el-tree__drop-indicator) { height: 2px; background-color: var(--c-workflow); border-radius: 1px; }
.tree-body :deep(.el-tree-node.is-drop-inner > .el-tree-node__content) { background: rgba(162,210,255,0.22) !important; box-shadow: inset 0 0 0 2px var(--c-workflow); }

.tree-node { display: flex; align-items: flex-start; gap: 5px; font-size: var(--app-size-sm); width: 100%; min-width: 0; user-select: none; line-height: 1.35; padding: 1px 0; }
.tree-node__icon { font-size: var(--app-size-sm); flex-shrink: 0; line-height: 1.35; margin-top: 1px; }
.tree-node__name { flex: 1; min-width: 0; color: var(--ink); font-weight: 500; }
.tree-node--l1 .tree-node__name, .tree-node--l2 .tree-node__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tree-node--case .tree-node__name { white-space: normal; word-break: break-word; overflow-wrap: anywhere; }
.tree-node__count { font-size: var(--app-size-xs); color: #999; background: rgba(162,210,255,0.14); padding: 0 6px; border-radius: 10px; font-weight: 600; flex-shrink: 0; line-height: 18px; margin-top: 1px; }
.tree-node--l1 .tree-node__name { font-weight: 700; color: var(--ink); }
.tree-node--case .tree-node__name { font-style: italic; font-weight: 500; color: #999; }
.tree-node--case-disabled .tree-node__name { color: #999; text-decoration: line-through; }

.tree-node__priority { font-size: var(--app-size-xs); font-weight: 700; padding: 1px 5px; border-radius: 6px; flex-shrink: 0; letter-spacing: 0.02em; line-height: 16px; margin-top: 1px; }
.tree-node__priority--p0 { background: rgba(224, 90, 90, 0.12); color: #c0392b; }
.tree-node__priority--p1 { background: rgba(245, 195, 28, 0.15); color: #8b6914; }
.tree-node__priority--p2 { background: rgba(162,210,255,0.14); color: #999; }

.context-menu { position: fixed; z-index: 1000; background: #fff; border: 1px solid var(--ink); border-radius: 14px; padding: 6px 0; min-width: 160px; box-shadow: var(--app-shadow-md); }
.context-menu__item { padding: 8px 16px; font-size: var(--app-size-sm); color: var(--ink); cursor: pointer; transition: background 0.15s ease; }
.context-menu__item:hover { background: rgba(162,210,255,0.16); color: var(--c-workflow); }
.context-menu__item--danger:hover { background: rgba(224, 90, 90, 0.1); color: #e05a5a; }
.context-menu__divider { height: 1px; background: rgba(162,210,255,0.24); margin: 4px 8px; }
</style>
