<script setup>
import { ref, watch, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Button as AnimalButton } from "animal-island-vue";
import { createDirectory, updateDirectory, deleteDirectory } from "../api.js";

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeId: { type: Number, default: null },
});

const emit = defineEmits(["select", "refresh"]);

const treeRef = ref(null);

// Show context menu
const menuVisible = ref(false);
const menuX = ref(0);
const menuY = ref(0);
const menuNode = ref(null);

// Rename / Create dialog
const dialogVisible = ref(false);
const dialogMode = ref("create"); // 'create' | 'rename'
const dialogName = ref("");
const dialogParentId = ref(null);
const dialogNodeId = ref(null);

// ── Tree node click ──
function handleNodeClick(data) {
  emit("select", data);
}

// ── Right-click context menu ──
function handleContextMenu(event, data) {
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

// ── Actions ──
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
  } catch (_) {}
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
  } catch (_) {}
}

// ── Tree node rendering ──
function nodeClass(data) {
  return {
    "tree-node--l1": data.parent_id === null,
    "tree-node--l2": data.parent_id !== null,
    "tree-node--active": data.id === props.activeId,
  };
}

// Close menu on outside click
function onDocumentClick() {
  if (menuVisible.value) closeMenu();
}

// Watch for outside clicks
if (typeof window !== "undefined") {
  window.addEventListener("click", onDocumentClick);
}
</script>

<template>
  <div class="directory-tree">
    <div class="tree-header">
      <span class="tree-header__title">📁 目录结构</span>
      <AnimalButton size="small" @click="openCreateRoot" title="新建一级目录"
        >+</AnimalButton
      >
    </div>

    <!-- el-tree -->
    <div class="tree-body">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        :expand-on-click-node="false"
        :highlight-current="true"
        :current-node-key="activeId"
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
      >
        <template #default="{ data }">
          <span class="tree-node" :class="nodeClass(data)">
            <span class="tree-node__icon">{{
              data.parent_id === null ? "📁" : "📂"
            }}</span>
            <span class="tree-node__name">{{ data.name }}</span>
            <span v-if="data.case_count > 0" class="tree-node__count">{{
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
      <div
        v-if="!menuNode || menuNode.parent_id === null"
        class="context-menu__item"
        @click="openCreateSub"
      >
        + 新建子目录
      </div>
      <div class="context-menu__item" @click="openRename">✏️ 重命名</div>
      <div class="context-menu__divider"></div>
      <div
        class="context-menu__item context-menu__item--danger"
        @click="handleDelete"
      >
        🗑️ 删除
      </div>
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
  padding: 16px;
  border-bottom: 2px solid rgba(139, 115, 85, 0.12);
}

.tree-header__title {
  font-weight: 700;
  font-size: 14px;
  color: #6b5b48;
  letter-spacing: 0.02em;
}

.tree-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* el-tree overrides */
.tree-body :deep(.el-tree) {
  background: transparent;
}

.tree-body :deep(.el-tree-node__content) {
  height: 36px;
  border-radius: 10px;
  padding-right: 8px;
}

.tree-body :deep(.el-tree-node__content:hover) {
  background: rgba(25, 200, 185, 0.08);
}

.tree-body :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(25, 200, 185, 0.14);
}

.tree-body
  :deep(.el-tree-node.is-current > .el-tree-node__content .tree-node__name) {
  color: #11a89b;
  font-weight: 700;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  width: 100%;
}

.tree-node__icon {
  font-size: 15px;
  flex-shrink: 0;
}

.tree-node__name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #725d42;
  font-weight: 500;
}

.tree-node__count {
  font-size: 11px;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.08);
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 600;
}

.tree-node--l1 .tree-node__name {
  font-weight: 700;
  color: #6b5b48;
}

.tree-node--l2 {
  padding-left: 4px;
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
</style>
