<script setup>
import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { ref, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiListApiEndpoints, apiCreateApiEndpoint, apiUpdateApiEndpoint, apiDeleteApiEndpoint } from "../api.js";
import { useApiGroupTree } from "../composables/useApiGroupTree.js";
import { usePagination } from "@/shared/composables/usePagination.js";

const methods = ["GET", "POST", "PUT", "DELETE", "PATCH"];
const METHOD_COLORS = { GET: "#6fba2c", POST: "#889df0", PUT: "#f7cd67", DELETE: "#e85f5f", PATCH: "#b39ef3" };

// ── Tree composable ──
const {
  groups, selectedGroup, endpoints, loading, treeRef,
  menuVisible, menuX, menuY, menuNode,
  showCreateGroup, createParentId, createIsFolder, newGroupForm,
  showRenameDialog, renameTarget, renameLabel,
  selectedGroupIds,
  dragEnabled, selectMode, moveDialogVisible, moveTargetDirId,
  groupTree, folderList,
  loadGroups, selectGroup,
  openCreateGroup, doCreateGroup,
  startEditLabel, doRename,
  deleteGroup,
  onNodeMouseDown, onNodeMouseUp, onNodeMouseLeave,
  allowDrag, allowDrop, handleNodeDrop,
  toggleSelectMode, handleSelectAll, openBatchMoveDialog, confirmBatchMove,
  handleContextMenu, closeMenu,
  handleTreeNodeClick, handleTreeCheck, nodeClass, nodeIcon, nodeName, groupLabel,
} = useApiGroupTree();

// ── Local filters ──
const searchText = ref("");
const methodFilter = ref("");

const filteredEndpoints = computed(() => {
  let list = endpoints.value;
  if (methodFilter.value) list = list.filter(e => e.method === methodFilter.value);
  if (searchText.value.trim()) {
    const q = searchText.value.trim().toLowerCase();
    list = list.filter(e =>
      (e.name || '').toLowerCase().includes(q) ||
      (e.url || '').toLowerCase().includes(q) ||
      (e.description || '').toLowerCase().includes(q) ||
      (e.tags || '').toLowerCase().includes(q)
    );
  }
  return list;
});

const { PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems, setPageSize, goPage } =
  usePagination(filteredEndpoints);

const columns = [
  { title: "名称", dataIndex: "name", key: "name", minWidth: 160 },
  { title: "方法", dataIndex: "method", key: "method", minWidth: 80, align: "center" },
  { title: "URL", dataIndex: "url", key: "url", minWidth: 300 },
  { title: "描述", dataIndex: "description", key: "description", minWidth: 180 },
  { title: "测试点", dataIndex: "is_test_point", key: "is_test_point", minWidth: 72, align: "center" },
  { title: "操作", dataIndex: "actions", key: "actions", minWidth: 110, align: "center" },
];

async function loadElements() {
  await selectGroup(selectedGroup.value);
}

async function updateEl(record, field, value) {
  try {
    const { data } = await apiUpdateApiEndpoint(record.id, { [field]: value });
    if (!data.ok) ElMessage.error(data.error || "更新失败");
  } catch (_) { ElMessage.error("更新失败"); }
}

async function doDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」吗？`, "删除确认",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" });
    await apiDeleteApiEndpoint(row.id);
    ElMessage.success("已删除");
    await loadElements();
  } catch (e) {
    if (e !== "cancel" && e?.message !== "cancel") ElMessage.error("删除失败");
  }
}

const showForm = ref(false);
const editingId = ref(null);
const form = ref({ name: "", method: "GET", url: "", headers: "{}", request_body_schema: "{}", response_body_schema: "{}", description: "", tags: "", is_test_point: false, group_id: null });
const headersStr = ref("{}");
const reqBodyStr = ref("{}");
const respBodyStr = ref("{}");

const nonFolderGroups = computed(() => groups.value.filter(g => !g.is_folder));

function openAdd() {
  editingId.value = null;
  form.value = {
    name: "", method: "GET", url: "", description: "", tags: "", is_test_point: false,
    group_id: selectedGroup.value && selectedGroup.value.id !== "__ungrouped__" ? selectedGroup.value.id : null,
  };
  headersStr.value = "{}"; reqBodyStr.value = "{}"; respBodyStr.value = "{}";
  showForm.value = true;
}

function openEdit(row) {
  editingId.value = row.id;
  form.value = {
    name: row.name, method: row.method, url: row.url,
    description: row.description || "", tags: row.tags || "",
    is_test_point: !!row.is_test_point, group_id: row.group_id || null,
  };
  try { headersStr.value = JSON.stringify(row.headers || {}, null, 2); } catch { headersStr.value = "{}"; }
  try { reqBodyStr.value = JSON.stringify(row.request_body_schema || {}, null, 2); } catch { reqBodyStr.value = "{}"; }
  try { respBodyStr.value = JSON.stringify(row.response_body_schema || {}, null, 2); } catch { respBodyStr.value = "{}"; }
  showForm.value = true;
}

async function doSave() {
  if (!form.value.name.trim() || !form.value.url.trim()) {
    ElMessage.warning("名称和 URL 必填"); return;
  }
  let headers = {}, reqBody = {}, respBody = {};
  try { headers = JSON.parse(headersStr.value); } catch { ElMessage.error("Headers JSON 格式无效"); return; }
  try { reqBody = JSON.parse(reqBodyStr.value); } catch { ElMessage.error("请求体 JSON 格式无效"); return; }
  try { respBody = JSON.parse(respBodyStr.value); } catch { ElMessage.error("响应体 JSON 格式无效"); return; }

  const payload = { ...form.value, headers, request_body_schema: reqBody, response_body_schema: respBody };
  try {
    if (editingId.value) {
      const { data } = await apiUpdateApiEndpoint(editingId.value, payload);
      if (data.ok) { showForm.value = false; await loadElements(); }
      else ElMessage.error(data.error || "更新失败");
    } else {
      const { data } = await apiCreateApiEndpoint(payload);
      if (data.ok) { showForm.value = false; await loadElements(); }
      else ElMessage.error(data.error || "创建失败");
    }
  } catch (e) { ElMessage.error(e?.response?.data?.error || "操作失败"); }
}
</script>

<template>
  <div class="api-endpoint-manager">
    <div class="main-layout">
      <!-- Left: Group Tree -->
      <aside class="tree-panel">
        <div v-if="!selectMode" class="tree-header">
          <span class="tree-header__title">接口分组</span>
          <div class="tree-header__actions">
            <el-button size="small" plain @click="openCreateGroup(null, true)">📁 + 项目</el-button>
            <el-button size="small" type="primary" @click="openCreateGroup(null, false)">📄 + 模块</el-button>
            <el-button size="small" plain @click="toggleSelectMode">☑ 选择</el-button>
          </div>
        </div>
        <div v-else class="tree-header tree-header--select">
          <span class="tree-header__title">已选 {{ selectedGroupIds.size }} 项</span>
          <div class="tree-header__actions">
            <el-button size="small" plain @click="handleSelectAll">☑ 全选</el-button>
            <el-button size="small" type="primary" :disabled="selectedGroupIds.size === 0" @click="openBatchMoveDialog">📂 移动</el-button>
            <el-button size="small" plain @click="toggleSelectMode">✕ 退出</el-button>
          </div>
        </div>

        <div class="tree-body" :class="{ 'drag-mode-active': dragEnabled }">
          <div v-if="loading && !groups.length" class="tree-loading">加载中...</div>
          <div v-else-if="!groups.length" class="tree-empty">
            <span class="tree-empty__icon">📁</span>
            <p class="tree-empty__text">暂无分组</p>
            <p class="tree-empty__hint">点击「+ 项目」或「+ 模块」创建</p>
          </div>
          <el-tree
            v-else
            ref="treeRef"
            :data="groupTree"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            :indent="16"
            :expand-on-click-node="true"
            :highlight-current="!selectMode"
            :current-node-key="selectedGroup?.id"
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
                <span class="tree-node__name" :title="data.name">{{ nodeName(data) }}</span>
                <span v-if="data.endpoint_count" class="tree-node__meta">{{ data.endpoint_count }} 接口</span>
                <span v-else-if="data.is_folder && data.child_count" class="tree-node__meta">{{ data.child_count }} 项</span>
              </span>
            </template>
          </el-tree>

          <!-- Ungrouped virtual node -->
          <div
            v-if="groups.length"
            class="tree-node tree-node--page ungrouped-node"
            :class="{ 'tree-node--active': selectedGroup?.id === '__ungrouped__' }"
            @click="selectGroup({ id: '__ungrouped__', name: '未分类', is_folder: false })"
          >
            <span class="tree-node__icon">📄</span>
            <span class="tree-node__name">未分类</span>
          </div>
        </div>
      </aside>

      <!-- Context menu -->
      <div v-if="menuVisible && menuNode" class="context-menu" :style="{ left: menuX + 'px', top: menuY + 'px' }" @click.stop>
        <template v-if="menuNode.is_folder">
          <div class="context-menu__item" @click="openCreateGroup(menuNode.id, true); closeMenu()">+ 新建子目录</div>
          <div class="context-menu__item" @click="openCreateGroup(menuNode.id, false); closeMenu()">+ 新建模块</div>
        </template>
        <div class="context-menu__item" @click="startEditLabel(menuNode); closeMenu()">✏️ 重命名</div>
        <div class="context-menu__divider" />
        <div class="context-menu__item context-menu__item--danger" @click="deleteGroup(menuNode); closeMenu()">🗑️ 删除</div>
      </div>

      <!-- Right: Endpoint table -->
      <template v-if="selectedGroup">
        <div class="endpoints-panel">
          <div class="panel-header">
            <h3 class="panel-title">
              {{ groupLabel(selectedGroup) }}
              <span class="doc-tag">API Endpoints</span>
            </h3>
            <div class="panel-header__actions">
              <el-button size="small" type="primary" @click="openAdd">+ 添加接口</el-button>
            </div>
          </div>

          <!-- Search / filter toolbar -->
          <div class="web-toolbar">
            <div class="web-toolbar__left">
              <el-input v-model="searchText" size="small" placeholder="搜索名称/URL/描述..." :allow-clear="true" style="width:240px">
                <template #prefix><span style="color:var(--app-ink)">🔍</span></template>
              </el-input>
              <el-select v-model="methodFilter" size="small" placeholder="请求方法" clearable style="width:110px">
                <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
              </el-select>
            </div>
          </div>

          <div class="table-area">
            <div class="table-toolbar">
              <div class="page-size-control">
                <span class="toolbar-label">显示行数</span>
                <div class="page-size-btns">
                  <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" type="button" class="page-size-btn"
                    :class="{ active: pageSize === n }" @click="setPageSize(n)">{{ n }}</button>
                </div>
              </div>
              <div v-if="filteredEndpoints.length > 0" class="table-toolbar-right">
                <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredEndpoints.length }} 条</span>
                <div v-if="totalPages > 1" class="page-nav">
                  <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                  <el-button size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                </div>
              </div>
            </div>
            <AppCard class="table-card">
              <div class="table-scroll">
                <AppTable :columns="columns" :data-source="pagedItems" row-key="id" :striped="true" :loading="loading"
                  empty-text="暂无 API 接口" class="endpoints-table">
                  <template #cell-name="{ record }">
                    <input class="cell-input" :value="record.name" placeholder="未命名"
                      @blur="(e) => updateEl(record, 'name', e.target.value)"
                      @keyup.enter="(e) => { updateEl(record, 'name', e.target.value); e.target.blur() }" />
                  </template>
                  <template #cell-method="{ value }">
                    <span :style="{ background: METHOD_COLORS[value] || 'var(--app-ink)' }"
                      style="display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;color:#fff">{{ value }}</span>
                  </template>
                  <template #cell-url="{ value }">
                    <span class="cell-code" :title="value">{{ value }}</span>
                  </template>
                  <template #cell-description="{ record }">
                    <input class="cell-input cell-input--desc" :value="record.description" placeholder="(无描述)"
                      @blur="(e) => updateEl(record, 'description', e.target.value)"
                      @keyup.enter="(e) => { updateEl(record, 'description', e.target.value); e.target.blur() }" />
                  </template>
                  <template #cell-is_test_point="{ record }">
                    <el-switch size="small" :model-value="record.is_test_point"
                      @update:model-value="(val) => updateEl(record, 'is_test_point', val)" />
                  </template>
                  <template #cell-actions="{ record }">
                    <div class="action-btns">
                      <el-button size="small" type="primary" link @click="openEdit(record)">编辑</el-button>
                      <el-button size="small" type="danger" link @click="doDelete(record)">删除</el-button>
                    </div>
                  </template>
                  <template #empty>
                    <div class="table-empty"><span>📡</span><p>暂无 API 接口</p><el-button size="small" type="primary" @click="openAdd">添加第一个接口</el-button></div>
                  </template>
                </AppTable>
              </div>
            </AppCard>
          </div>
          <span class="element-count">共 {{ endpoints.length }} 个接口</span>
        </div>
      </template>
      <AppCard v-else class="empty-card">
        <div class="empty-state">← 选择左侧分组查看接口</div>
      </AppCard>
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showForm" :title="editingId ? '编辑接口' : '添加接口'" width="620px" :close-on-click-modal="false">
      <div class="form-grid">
        <label class="form-label required">名称</label><el-input v-model="form.name" placeholder="如：用户登录" size="middle" />
        <label class="form-label">所属分组</label>
        <el-select v-model="form.group_id" placeholder="选择分组（可选）" clearable style="width: 100%" size="middle">
          <el-option v-for="g in nonFolderGroups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <label class="form-label required">方法</label>
        <el-select v-model="form.method" style="width:100%" size="middle">
          <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
        </el-select>
        <label class="form-label required">URL</label><el-input v-model="form.url" placeholder="https://api.example.com/login" size="middle" />
        <label class="form-label">Headers</label>
        <el-input v-model="headersStr" type="textarea" :rows="3" placeholder='{"Content-Type":"application/json"}' size="middle" />
        <label class="form-label">请求体</label>
        <el-input v-model="reqBodyStr" type="textarea" :rows="4" placeholder='{"username":"string","password":"string"}' size="middle" />
        <label class="form-label">响应体</label>
        <el-input v-model="respBodyStr" type="textarea" :rows="4" placeholder='{"token":"string","user":{"id":1,"name":"string"}}' size="middle" />
        <label class="form-label">描述</label><el-input v-model="form.description" placeholder="接口用途" size="middle" />
        <label class="form-label">标签</label><el-input v-model="form.tags" placeholder="逗号分隔" size="middle" />
        <label class="form-label">测试点</label><el-switch v-model="form.is_test_point" size="medium" />
      </div>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="doSave">{{ editingId ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- Create Group -->
    <el-dialog v-model="showCreateGroup" :title="createIsFolder ? '新建项目目录' : '新建模块'" width="360px" :close-on-click-modal="false">
      <div class="form-grid">
        <label class="form-label required">名称</label>
        <el-input v-model="newGroupForm.name" :placeholder="createIsFolder ? '如：电商项目' : '如：用户模块'" size="middle"
          @keyup.enter="doCreateGroup" />
      </div>
      <template #footer>
        <el-button @click="showCreateGroup = false">取消</el-button>
        <el-button type="primary" @click="doCreateGroup">创建</el-button>
      </template>
    </el-dialog>

    <!-- Rename Group -->
    <el-dialog v-model="showRenameDialog" :title="renameTarget?.is_folder ? '重命名项目' : '重命名模块'" width="360px"
      :close-on-click-modal="false">
      <div class="form-grid">
        <label class="form-label required">名称</label>
        <el-input v-model="renameLabel" placeholder="输入新名称" size="middle" @keyup.enter="doRename" />
      </div>
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="doRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch Move -->
    <el-dialog v-model="moveDialogVisible" title="选择目标目录" width="420px" :close-on-click-modal="false">
      <el-select v-model="moveTargetDirId" placeholder="选择要移动到的目录" filterable style="width: 100%">
        <el-option v-for="dir in folderList" :key="dir.id" :label="dir.label" :value="dir.id" />
      </el-select>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!moveTargetDirId" @click="confirmBatchMove">确认移动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ── Root ── */
.api-endpoint-manager { background: radial-gradient(circle, var(--app-paper-dot, #d4cdc0) 0.8px, transparent 0.8px); background-size: 14px 14px; background-color: var(--app-paper, #fefcf6);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  padding: 16px 20px 20px;
  height: 100%;
}

.main-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  height: 100%;
  flex: 1;
  min-height: 0;
}

/* ── Tree Panel ── */
.tree-panel { background: radial-gradient(circle, var(--app-paper-dot, #d4cdc0) 0.8px, transparent 0.8px); background-size: 14px 14px; background-color: var(--app-paper, #fefcf6);
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  overflow: hidden;
  min-height: 0;
}

.tree-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.tree-header--select {
  background: rgba(179, 158, 243, 0.08);
}

.tree-header__title {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-ink);
}

.tree-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tree-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px 4px 10px;
  min-height: 0;
}

.tree-body.drag-mode-active {
  cursor: grab;
}

.tree-loading,
.tree-empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--app-ink-muted);
  font-size: 13px;
}

.tree-empty__icon {
  display: block;
  font-size: 32px;
  margin-bottom: 8px;
}

.tree-empty__text {
  font-weight: 600;
  color: var(--app-ink);
  margin: 0 0 4px;
}

.tree-empty__hint {
  font-size: 12px;
  color: var(--app-ink-muted);
  margin: 0;
}

/* Tree node */
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.tree-node__icon {
  font-size: 14px;
  flex-shrink: 0;
}

.tree-node__name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--app-ink);
}

.tree-node--folder .tree-node__name {
  font-weight: 600;
  color: var(--app-ink);
}

.tree-node--active .tree-node__name {
  color: var(--app-accent-purple-dark);
  font-weight: 700;
}

.tree-node__meta {
  font-size: 11px;
  color: var(--app-ink-muted);
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 6px;
  border-radius: 4px 8px 4px 8px;
  flex-shrink: 0;
}

.ungrouped-node {
  padding: 6px 14px;
  margin-top: 4px;
  border-top: 1px dashed rgba(0, 0, 0, 0.12);
  cursor: pointer;
  border-radius: 6px;
}

.ungrouped-node:hover {
  background: rgba(0, 0, 0, 0.06);
}

.ungrouped-node.tree-node--active {
  background: rgba(179, 158, 243, 0.12);
}

/* ── Context Menu ── */
.context-menu {
  position: fixed;
  z-index: 3000;
  background: #fff;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  min-width: 140px;
  padding: 4px 0;
}

.context-menu__item {
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--app-ink);
}

.context-menu__item:hover {
  background: rgba(0, 0, 0, 0.06);
}

.context-menu__item--danger {
  color: var(--app-status-danger-text);
}

.context-menu__divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 4px 8px;
}

/* ── Endpoints Panel ── */
.endpoints-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  gap: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}

.panel-header__actions {
  display: flex;
  gap: 8px;
}

.panel-title { font-family: "Caveat", cursive;
  font-size: 15px;
  font-weight: 700;
  color: var(--app-ink);
  margin: 0;
}

.doc-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  background: rgba(0, 0, 0, 0.1);
  color: var(--app-ink);
  padding: 2px 8px;
  border-radius: 6px 10px 6px 10px;
  margin-left: 8px;
  vertical-align: middle;
}

.web-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.web-toolbar__left, .web-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
}

.empty-state {
  font-size: 14px;
  color: var(--app-ink-muted);
}

/* ── Table Area ── */
.table-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.page-size-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-ink-muted);
}

.page-size-btns {
  display: flex;
  gap: 6px;
}

.page-size-btn {
  min-width: 40px;
  padding: 4px 10px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  border: 3px solid var(--app-ink, #2d2d2d);
  background: #fff;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-ink);
  cursor: pointer;
  transition: all 0.2s;
}

.page-size-btn:hover {
  border-color: var(--app-accent-purple);
  color: var(--app-accent-purple);
}

.page-size-btn.active {
  background: rgba(179, 158, 243, 0.12);
  border-color: var(--app-accent-purple);
  color: var(--app-accent-purple);
}

.table-toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.page-info {
  font-size: 12px;
  color: var(--app-ink-muted);
}

.page-nav {
  display: flex;
  gap: 8px;
}

.table-card {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.table-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.table-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;
  width: 100%;
}

/* ── Cell Styles ── */
.cell-input {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--app-accent-purple);
  font-weight: 600;
  padding: 4px 6px;
  border-radius: 4px;
  outline: none;
}

.cell-input:hover, .cell-input:focus {
  background: rgba(179, 158, 243, 0.06);
}

.cell-input--desc {
  color: var(--app-ink);
  font-weight: 400;
  font-size: 12px;
}

.cell-code {
  font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
  font-size: 12px;
  color: #8275c2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 280px;
}

.action-btns {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.element-count {
  font-size: 12px;
  color: var(--app-ink-muted);
  text-align: right;
  flex-shrink: 0;
}

.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 0;
}

.table-empty span {
  font-size: 36px;
}

.table-empty p {
  font-size: 15px;
  color: var(--app-ink-muted);
  margin: 0;
}

/* ── Form Grid ── */
.form-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 14px 10px;
  align-items: center;
}

.form-label {
  font-size: 13px;
  color: var(--app-ink-muted);
  text-align: right;
}

.form-label.required::before {
  content: "*";
  color: var(--app-status-danger-text);
  margin-right: 2px;
}

/* Paper table headers */
.endpoint-table :deep(.el-table__header th) {
  background: var(--app-accent-purple) !important; color: #fff !important;
  font-size: 10px; font-weight: 700; padding: 6px 10px;
  border-right: 2px solid var(--doodle-ink);
}
.endpoint-table :deep(.el-table__header th:first-child) { border-radius: 3px 0 0 0; }
.endpoint-table :deep(.el-table__header th:last-child) { border-radius: 0 3px 0 0; border-right: none; }
</style>
