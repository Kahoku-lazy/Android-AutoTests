<script setup>
import { ref, watch, nextTick, computed, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
// Button → el-button (Element Plus auto-import);
import EmptyState from "@/shared/components/patterns/EmptyState.vue";
import { formatApiError } from "@/shared/api-client.js";
import {
  createDirectory,
  updateDirectory,
  deleteDirectory,
  deleteDefinition,
  batchMoveItems,
} from "../api.js";

const router = useRouter();

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeId: { type: Number, default: null },
});

const emit = defineEmits(["select", "refresh"]);

const treeRef = ref(null);

// ── Context menu ──
const menuVisible = ref(false);
const menuX = ref(0);
const menuY = ref(0);
const menuNode = ref(null);

// ── Rename / Create dialog ──
const dialogVisible = ref(false);
const dialogMode = ref("create");
const dialogName = ref("");
const dialogParentId = ref(null);
const dialogNodeId = ref(null);

// ── Long-press drag ──
const dragEnabled = ref(false);
const longPressTimer = ref(null);
const dragSourceNode = ref(null);

// ── Batch selection ──
const selectMode = ref(false);
const checkedIds = ref(new Set());
const selectAll = ref(false);

// ── Batch move dialog ──
const moveDialogVisible = ref(false);
const moveTargetDirId = ref(null);

// Flatten tree to collect all checkable nodes
function collectNodes(nodes, result = []) {
  for (const node of nodes) {
    if (node.node_type !== "case" || node.enabled !== false) {
      result.push(node);
    }
    if (node.children && node.children.length > 0) {
      collectNodes(node.children, result);
    }
  }
  return result;
}

const allCheckableIds = computed(() => {
  return collectNodes([...props.treeData]).map((n) => String(n.id));
});

const checkedCount = computed(() => checkedIds.value.size);

// ── Tree node click ──
function handleNodeClick(data) {
  if (selectMode.value) return; // ignore clicks in select mode
  emit("select", data);
}

// ── Right-click context menu ──
function handleContextMenu(event, data) {
  if (selectMode.value) return;
  event.preventDefault();
  menuNode.value = data;
  menuX.value = event.clientX;
  menuY.value = event.clientY;
  menuVisible.value = true;
}

function closeMenu() {
  menuVisible.value = false;
  menuNode.value = null;
}

// ── Long-press drag detection ──
function onNodeMouseDown(e, data) {
  if (selectMode.value) return;
  // Only for right-click on context menu
  // Left-click: start long-press timer
  if (e.button !== 0) return;
  dragSourceNode.value = data;
  longPressTimer.value = setTimeout(() => {
    dragEnabled.value = true;
    // Add visual feedback to tree
    if (treeRef.value) {
      const el = treeRef.value.$el;
      el.classList.add("drag-mode-active");
    }
  }, 500);
}

function onNodeMouseUp() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value);
    longPressTimer.value = null;
  }
}

function onNodeMouseLeave() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value);
    longPressTimer.value = null;
  }
}

// ── el-tree drag handlers ──
function allowDrag(node) {
  return dragEnabled.value;
}

function allowDrop(draggingNode, dropNode, type) {
  // Can drop into directories (inner), or between nodes (before/after)
  const target = dropNode.data;
  // Don't allow dropping a directory into itself or its descendants
  if (type === "inner" && target.node_type !== "directory") return false;
  return true;
}

async function handleNodeDrop(draggingNode, dropNode, dropType) {
  const source = draggingNode.data;
  const target = dropNode.data;

  // Reset drag state
  dragEnabled.value = false;
  dragSourceNode.value = null;
  if (treeRef.value) {
    treeRef.value.$el.classList.remove("drag-mode-active");
  }

  // Determine target directory
  let targetDirId;
  let targetDirName;
  if (dropType === "inner") {
    targetDirId = target.id;
    targetDirName = target.name;
  } else {
    // before/after: move to the target's parent directory
    targetDirId = target.parent_id;
    targetDirName = ""; // will use parent name from tree
  }

  if (targetDirId === undefined || targetDirId === null) {
    ElMessage.warning("不能移动到根级，请选择一个目录");
    return;
  }

  const sourceName = source.name || source.case_id || source.id;
  const sourceType = source.node_type === "case" ? "用例" : "目录";

  // Confirmation dialog
  try {
    await ElMessageBox.confirm(
      `将${sourceType}「${sourceName}」移动到目标位置？`,
      "确认移动",
      {
        confirmButtonText: "确认移动",
        cancelButtonText: "取消",
        type: "warning",
      },
    );
  } catch (_) {
    return; // user cancelled
  }

  // Execute move
  const items = [
    {
      type: source.node_type === "case" ? "case" : "directory",
      id: source.node_type === "case" ? source.case_id : source.id,
    },
  ];
  try {
    const { data } = await batchMoveItems(items, targetDirId);
    if (data.ok) {
      if (data.errors && data.errors.length > 0) {
        data.errors.forEach((e) => ElMessage.error(`${e.id}: ${e.reason}`));
      }
      if (data.moved > 0) {
        ElMessage.success(`已移动 ${data.moved} 项`);
        emit("refresh");
      }
    } else {
      ElMessage.error(data.error || "移动失败");
    }
  } catch (e) {
    ElMessage.error(formatApiError(e, "移动失败"));
  }
}

// ── Select mode ──
function toggleSelectMode() {
  selectMode.value = !selectMode.value;
  if (!selectMode.value) {
    checkedIds.value = new Set();
    selectAll.value = false;
  }
}

function handleCheck() {
  // Sync checked state from tree after check change
  nextTick(() => {
    if (treeRef.value) {
      const keys = treeRef.value.getCheckedKeys().map(String);
      checkedIds.value = new Set(keys);
      selectAll.value = keys.length === allCheckableIds.value.length;
    }
  });
}

function handleSelectAll() {
  if (selectAll.value) {
    checkedIds.value = new Set();
    selectAll.value = false;
    if (treeRef.value) treeRef.value.setCheckedKeys([]);
  } else {
    const allIds = allCheckableIds.value;
    checkedIds.value = new Set(allIds);
    selectAll.value = true;
    if (treeRef.value) treeRef.value.setCheckedKeys(allIds);
  }
}

function openBatchMoveDialog() {
  if (checkedIds.value.size === 0) {
    ElMessage.warning("请先选择要移动的用例或目录");
    return;
  }
  moveTargetDirId.value = null;
  moveDialogVisible.value = true;
}

async function confirmBatchMove() {
  if (!moveTargetDirId.value) {
    ElMessage.warning("请选择目标目录");
    return;
  }

  const items = [];
  for (const id of checkedIds.value) {
    // Find the node to determine type
    const node = findNodeById(props.treeData, id);
    if (node) {
      items.push({
        type: node.node_type === "case" ? "case" : "directory",
        id: node.node_type === "case" ? node.case_id : node.id,
      });
    }
  }

  if (items.length === 0) return;

  try {
    await ElMessageBox.confirm(
      `确认将 ${items.length} 项移动到目标位置？`,
      "批量移动",
      {
        confirmButtonText: "确认移动",
        cancelButtonText: "取消",
        type: "warning",
      },
    );
  } catch (_) {
    return;
  }

  try {
    const { data } = await batchMoveItems(items, Number(moveTargetDirId.value));
    if (data.ok) {
      if (data.errors && data.errors.length > 0) {
        data.errors.forEach((e) => ElMessage.error(`${e.id}: ${e.reason}`));
      }
      if (data.moved > 0) {
        ElMessage.success(`已移动 ${data.moved} 项`);
      }
      moveDialogVisible.value = false;
      selectMode.value = false;
      checkedIds.value = new Set();
      selectAll.value = false;
      emit("refresh");
    } else {
      ElMessage.error(data.error || "批量移动失败");
    }
  } catch (e) {
    ElMessage.error(formatApiError(e, "批量移动失败"));
  }
}

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

// Collect flat directory list for move target picker
const dirList = computed(() => {
  const result = [];
  function walk(nodes) {
    for (const node of nodes) {
      if (node.node_type !== "case") {
        result.push({
          id: node.id,
          name: node.name,
          parent_id: node.parent_id,
        });
      }
      if (node.children) walk(node.children);
    }
  }
  walk(props.treeData);
  return result;
});

// ── Context menu actions ──
function openCreateSub() {
  dialogMode.value = "create";
  dialogName.value = "";
  dialogParentId.value = menuNode.value ? menuNode.value.id : null;
  dialogNodeId.value = null;
  dialogVisible.value = true;
  closeMenu();
}

function openCreateRoot() {
  dialogMode.value = "create";
  dialogName.value = "";
  dialogParentId.value = null;
  dialogNodeId.value = null;
  dialogVisible.value = true;
}

function openRename() {
  if (!menuNode.value) return;
  dialogMode.value = "rename";
  dialogName.value = menuNode.value.name;
  dialogNodeId.value = menuNode.value.id;
  dialogParentId.value = null;
  dialogVisible.value = true;
  closeMenu();
}

async function handleDelete() {
  if (!menuNode.value) return;
  const node = menuNode.value;
  closeMenu();
  try {
    await ElMessageBox.confirm(
      `确定删除目录「${node.name}」？${node.children && node.children.length > 0 ? "注意：该目录下存在子目录或用例，需先清空。" : ""}`,
      "确认删除",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    );
    const { data } = await deleteDirectory(node.id);
    if (data.ok) {
      ElMessage.success("已删除");
      emit("refresh");
    } else {
      ElMessage.error(data.error || "删除失败");
    }
  } catch (e) {
    ElMessage.error(formatApiError(e, "删除失败"));
  }
}

function goCreateCase() {
  if (!menuNode.value) return;
  const dirId = menuNode.value.id;
  closeMenu();
  router.push({ path: "/cases/new", query: { directory_id: dirId } });
}

function goEditCase() {
  if (!menuNode.value) return;
  const caseId = menuNode.value.case_id;
  closeMenu();
  router.push(`/cases/${caseId}/edit`);
}

async function handleDeleteCase() {
  if (!menuNode.value) return;
  const node = menuNode.value;
  closeMenu();
  try {
    await ElMessageBox.confirm(`确定删除用例「${node.name}」？`, "确认删除", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    const { data } = await deleteDefinition(node.case_id);
    if (data.ok) {
      ElMessage.success("已删除");
      emit("refresh");
    } else {
      ElMessage.error(data.error || "删除失败");
    }
  } catch (e) {
    if (e !== "cancel" && e?.message !== "cancel")
      ElMessage.error(formatApiError(e, "删除失败"));
  }
}

// ── Dialog confirm ──
async function handleDialogConfirm() {
  if (!dialogName.value.trim()) {
    ElMessage.warning("请输入目录名称");
    return;
  }
  try {
    if (dialogMode.value === "create") {
      const { data } = await createDirectory(
        dialogName.value.trim(),
        dialogParentId.value,
      );
      if (data.ok) {
        ElMessage.success("目录已创建");
      } else {
        ElMessage.error(data.error || "创建失败");
        return;
      }
    } else {
      const { data } = await updateDirectory(dialogNodeId.value, {
        name: dialogName.value.trim(),
      });
      if (data.ok) {
        ElMessage.success("目录已更新");
      } else {
        ElMessage.error(data.error || "更新失败");
        return;
      }
    }
    dialogVisible.value = false;
    emit("refresh");
  } catch (e) {
    ElMessage.error(formatApiError(e, "操作失败"));
  }
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

// Close menu on outside click
function onDocumentClick() {
  if (menuVisible.value) closeMenu();
}

if (typeof window !== "undefined") {
  window.addEventListener("click", onDocumentClick);
}
// B11修复: 组件卸载时清理全局监听
onUnmounted(() => {
  window.removeEventListener("click", onDocumentClick);
});
</script>

<template>
  <div class="directory-tree">
    <!-- Normal header -->
    <div v-if="!selectMode" class="tree-header">
      <span class="tree-header__title">📁 目录结构</span>
      <div class="tree-header__actions">
        <el-button
          size="small"
          type="primary"
          @click="toggleSelectMode"
          title="批量选择"
          >☑ 选择</el-button
        >
        <el-button size="small" @click="openCreateRoot" title="新建一级目录"
          >+</el-button
        >
      </div>
    </div>

    <!-- Select mode header -->
    <div v-else class="tree-header tree-header--select">
      <span class="tree-header__title">已选 {{ checkedCount }} 项</span>
      <div class="tree-header__actions">
        <el-button size="small" @click="handleSelectAll">
          {{ selectAll ? "☐ 取消全选" : "☑ 全选" }}
        </el-button>
        <el-button
          size="small"
          type="primary"
          :disabled="checkedCount === 0"
          @click="openBatchMoveDialog"
          >📂 移动到...</el-button
        >
        <el-button size="small" @click="toggleSelectMode"
          >✕ 退出选择</el-button
        >
      </div>
    </div>

    <!-- el-tree -->
    <div class="tree-body">
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
            @mousedown="onNodeMouseDown($event, data)"
            @mouseup="onNodeMouseUp"
            @mouseleave="onNodeMouseLeave"
          >
            <span class="tree-node__icon">{{ nodeIcon(data) }}</span>
            <span class="tree-node__name" :title="data.name">{{ data.name }}</span>
            <span
              v-if="data.node_type === 'case'"
              class="tree-node__priority"
              :class="
                'tree-node__priority--' + (data.priority || 'P1').toLowerCase()
              "
              >{{ data.priority }}</span
            >
            <span v-else-if="data.case_count > 0" class="tree-node__count">{{
              data.case_count
            }}</span>
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
      <!-- Directory node menu items -->
      <template v-if="!menuNode || menuNode.node_type !== 'case'">
        <div
          v-if="menuNode && menuNode.parent_id === null"
          class="context-menu__item"
          @click="openCreateSub"
        >
          + 新建子目录
        </div>
        <!-- 新建用例：一级和二级都显示 -->
        <div v-if="menuNode" class="context-menu__item" @click="goCreateCase">
          📋 新建用例
        </div>
        <div class="context-menu__item" @click="openRename">✏️ 重命名</div>
        <div class="context-menu__divider"></div>
        <div
          class="context-menu__item context-menu__item--danger"
          @click="handleDelete"
        >
          🗑️ 删除
        </div>
      </template>

      <!-- Case node menu items -->
      <template v-else>
        <div class="context-menu__item" @click="goEditCase">📝 编辑用例</div>
        <div class="context-menu__divider"></div>
        <div
          class="context-menu__item context-menu__item--danger"
          @click="handleDeleteCase"
        >
          🗑️ 删除用例
        </div>
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
        :placeholder="
          dialogMode === 'create' ? '输入目录名称，如：开关功能' : '输入新名称'
        "
        maxlength="200"
        @keyup.enter="handleDialogConfirm"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDialogConfirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch move target picker -->
    <el-dialog
      v-model="moveDialogVisible"
      title="选择目标目录"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-select
        v-model="moveTargetDirId"
        placeholder="选择要移动到的目录"
        style="width: 100%"
      >
        <el-option
          v-for="dir in dirList"
          :key="dir.id"
          :label="(dir.parent_id ? '  📂 ' : '📁 ') + dir.name"
          :value="dir.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!moveTargetDirId"
          @click="confirmBatchMove"
          >确认移动</el-button>
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
  border-bottom: 2px solid rgba(139, 115, 85, 0.12);
  flex-shrink: 0;
}

.tree-header--select {
  background: rgba(25, 200, 185, 0.06);
}

.tree-header__title {
  font-weight: 700;
  font-size: 13px;
  color: #6b5b48;
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

/* el-tree overrides */
.tree-body :deep(.el-tree) {
  background: transparent;
}

.tree-body :deep(.el-tree-node__content) {
  height: auto;
  min-height: 32px;
  border-radius: 8px;
  padding: 3px 6px 3px 2px;
  transition: background 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.tree-body :deep(.el-tree-node__expand-icon) {
  padding: 4px;
  font-size: 12px;
}

.tree-body :deep(.el-tree-node__content:hover) {
  background: rgba(25, 200, 185, 0.08);
}

.tree-body :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(25, 200, 185, 0.14);
}

/* Drag mode visual feedback */
.tree-body.drag-mode-active :deep(.el-tree-node__content) {
  cursor: grab;
}

.tree-body.drag-mode-active :deep(.el-tree-node__content:active) {
  cursor: grabbing;
}

/* Drop indicator style */
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
  align-items: flex-start;
  gap: 5px;
  font-size: 13px;
  width: 100%;
  min-width: 0;
  user-select: none;
  line-height: 1.35;
  padding: 1px 0;
}

.tree-node__icon {
  font-size: 14px;
  flex-shrink: 0;
  line-height: 1.35;
  margin-top: 1px;
}

.tree-node__name {
  flex: 1;
  min-width: 0;
  color: #725d42;
  font-weight: 500;
}

.tree-node--l1 .tree-node__name,
.tree-node--l2 .tree-node__name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tree-node--case .tree-node__name {
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.tree-node__count {
  font-size: 10px;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.08);
  padding: 0 6px;
  border-radius: 10px;
  font-weight: 600;
  flex-shrink: 0;
  line-height: 18px;
  margin-top: 1px;
}

.tree-node--l1 .tree-node__name {
  font-weight: 700;
  color: #6b5b48;
}

.tree-node--l2 {
  padding-left: 0;
}

.tree-node--case {
  padding-left: 0;
}

.tree-node--case .tree-node__name {
  font-style: italic;
  font-weight: 500;
  color: #725d42;
}

.tree-node--case-disabled .tree-node__name {
  color: #c4b89e;
  text-decoration: line-through;
}

.tree-node__priority {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 6px;
  flex-shrink: 0;
  letter-spacing: 0.02em;
  line-height: 16px;
  margin-top: 1px;
}

.tree-node__priority--p0 {
  background: rgba(224, 90, 90, 0.12);
  color: #c0392b;
}
.tree-node__priority--p1 {
  background: rgba(245, 195, 28, 0.15);
  color: #8b6914;
}
.tree-node__priority--p2 {
  background: rgba(139, 115, 85, 0.08);
  color: #9f927d;
}

/* Context menu */
.context-menu {
  position: fixed;
  z-index: 1000;
  background: rgb(247, 243, 223);
  border: 2px solid #c4b89e;
  border-radius: 14px;
  padding: 6px 0;
  min-width: 160px;
  box-shadow: 0 4px 16px rgba(61, 52, 40, 0.12);
}

.context-menu__item {
  padding: 8px 16px;
  font-size: 13px;
  color: #725d42;
  cursor: pointer;
  transition: background 0.15s ease;
}

.context-menu__item:hover {
  background: rgba(25, 200, 185, 0.1);
  color: #19c8b9;
}

.context-menu__item--danger:hover {
  background: rgba(224, 90, 90, 0.1);
  color: #e05a5a;
}

.context-menu__divider {
  height: 1px;
  background: rgba(196, 184, 158, 0.4);
  margin: 4px 8px;
}

/* Empty state */
.tree-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
}

.tree-empty__icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.tree-empty__text {
  font-size: 14px;
  font-weight: 600;
  color: #988b7a;
  margin: 0 0 6px;
}

.tree-empty__hint {
  font-size: 12px;
  color: #c4b89e;
  margin: 0;
}
</style>
