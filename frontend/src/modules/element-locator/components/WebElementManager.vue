<script setup>
import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { ref, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  apiListWebElements,
  apiCreateWebElement,
  apiUpdateWebElement,
  apiDeleteWebElement,
  apiBatchImportWebElements,
  apiListWebFlows,
  apiCreateWebFlow,
  apiDeleteWebFlow,
} from "../api.js";
import { useWebGroupTree } from "../composables/useWebGroupTree.js";
import { usePagination } from "@/shared/composables/usePagination.js";

const LOCATOR_TYPES = [
  { value: "css_selector", label: "CSS Selector", hint: ".class, #id, div > p" },
  { value: "xpath", label: "XPath", hint: "//div[@id='app']/button" },
  { value: "id", label: "ID", hint: "login-button" },
  { value: "class_name", label: "Class Name", hint: "login-btn" },
  { value: "name", label: "Name", hint: "username" },
  { value: "tag_name", label: "Tag Name", hint: "input, button, div" },
  { value: "link_text", label: "Link Text", hint: "忘记密码" },
  { value: "partial_link_text", label: "Partial Link Text", hint: "忘记" },
  { value: "text", label: "Text Content", hint: "登录 (Playwright getByText)" },
  { value: "test_id", label: "Test ID", hint: "data-testid 属性值" },
  { value: "role", label: "ARIA Role", hint: "button, link, textbox" },
  { value: "placeholder", label: "Placeholder", hint: "请输入用户名" },
];
const LOCATOR_LABEL_MAP = Object.fromEntries(LOCATOR_TYPES.map((t) => [t.value, t.label]));

// ── Tree composable ──
const {
  groups, selectedGroup, elements, loading, treeRef,
  menuVisible, menuX, menuY, menuNode,
  showCreateGroup, createParentId, createIsFolder, newGroupForm,
  showRenameDialog, renameTarget, renameLabel,
  selectedGroupIds, showClearDialog,
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
} = useWebGroupTree();

// ── Element table ──
const filterMode = ref("all");
const filterTabs = [
  { key: "all", label: "全部" },
  { key: "test_point", label: "测试点" },
];
const filteredElements = computed(() =>
  filterMode.value === "test_point" ? elements.value.filter((e) => e.is_test_point) : elements.value
);

const { PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems: pagedElements, setPageSize, goPage } =
  usePagination(filteredElements);

const columns = [
  { title: "名称", dataIndex: "name", key: "name", minWidth: 140 },
  { title: "定位方式", dataIndex: "locator_type", key: "locator_type", minWidth: 110 },
  { title: "定位值", dataIndex: "locator_value", key: "locator_value", minWidth: 260 },
  { title: "页面 URL", dataIndex: "page_url", key: "page_url", minWidth: 180 },
  { title: "描述", dataIndex: "description", key: "description", minWidth: 140 },
  { title: "测试点", dataIndex: "is_test_point", key: "is_test_point", minWidth: 72, align: "center" },
  { title: "操作", dataIndex: "actions", key: "actions", minWidth: 110, align: "center" },
];

async function updateEl(record, field, value) {
  try {
    const { data } = await apiUpdateWebElement(record.id, { [field]: value });
    if (!data.ok) ElMessage.error(data.error || "更新失败");
  } catch (_) { ElMessage.error("更新失败，请检查网络"); }
}

async function doDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除「${row.name}」吗？`, "删除确认", {
      confirmButtonText: "确定删除", cancelButtonText: "取消", type: "warning",
    });
    await apiDeleteWebElement(row.id);
    ElMessage.success("已删除");
    await loadElements();
  } catch (e) {
    if (e !== "cancel" && e?.message !== "cancel") ElMessage.error("删除失败");
  }
}

async function loadElements() {
  await selectGroup(selectedGroup.value);
  if (selectedGroup.value && selectedGroup.value.id !== '__ungrouped__') {
    await loadFlows();
  } else {
    flows.value = [];
  }
}

// ── Page Flows ──
const flows = ref([]);
const showFlowDialog = ref(false);
const newFlowForm = ref({ from_group_id: null, to_group_id: null, trigger_element_id: null, trigger_action: 'click' });

async function loadFlows() {
  try {
    const { data } = await apiListWebFlows();
    if (data.ok) {
      const gid = selectedGroup.value?.id;
      flows.value = (data.flows || []).filter(
        f => f.from_group_id === gid || f.to_group_id === gid
      );
    }
  } catch (_) { flows.value = []; }
}

function openAddFlow() {
  newFlowForm.value = {
    from_group_id: selectedGroup.value?.id || null,
    to_group_id: null,
    trigger_element_id: null,
    trigger_action: 'click',
  };
  showFlowDialog.value = true;
}

async function doCreateFlow() {
  const f = newFlowForm.value;
  if (!f.from_group_id || !f.to_group_id) {
    ElMessage.warning('请选择源页面和目标页面');
    return;
  }
  try {
    const { data } = await apiCreateWebFlow(f);
    if (data.ok) { showFlowDialog.value = false; await loadFlows(); }
    else ElMessage.error(data.error || '创建失败');
  } catch (e) { ElMessage.error(e?.response?.data?.error || '创建失败'); }
}

async function doDeleteFlow(flow) {
  try {
    await ElMessageBox.confirm(
      `断开「${flow.from_label} → ${flow.to_label}」的连接？`,
      '断开连接', { confirmButtonText: '确认断开', cancelButtonText: '取消', type: 'warning' }
    );
    await apiDeleteWebFlow(flow.id);
    ElMessage.success('已断开');
    await loadFlows();
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') ElMessage.error('断开失败');
  }
}

// ── Add/Edit dialog ──
const showFormDialog = ref(false);
const editingId = ref(null);
const formTitle = computed(() => (editingId.value ? "编辑元素" : "添加元素"));
const form = ref({
  name: "", locator_type: "css_selector", locator_value: "",
  page_url: "", description: "", tags: "", is_test_point: false, group_id: null,
});
const selectedLocator = computed(() => LOCATOR_TYPES.find((t) => t.value === form.value.locator_type) || LOCATOR_TYPES[0]);

function openAdd() {
  editingId.value = null;
  form.value = {
    name: "", locator_type: "css_selector", locator_value: "",
    page_url: "", description: "", tags: "", is_test_point: false,
    group_id: selectedGroup.value && selectedGroup.value.id !== "__ungrouped__" ? selectedGroup.value.id : null,
  };
  showFormDialog.value = true;
}

function openEdit(row) {
  editingId.value = row.id;
  form.value = {
    name: row.name || "", locator_type: row.locator_type || "css_selector",
    locator_value: row.locator_value || "", page_url: row.page_url || "",
    description: row.description || "", tags: row.tags || "",
    is_test_point: !!row.is_test_point, group_id: row.group_id || null,
  };
  showFormDialog.value = true;
}

async function doSave() {
  if (!form.value.name.trim()) { ElMessage.warning("请输入元素名称"); return; }
  if (!form.value.locator_value.trim()) { ElMessage.warning("请输入定位值"); return; }
  try {
    if (editingId.value) {
      const { data } = await apiUpdateWebElement(editingId.value, form.value);
      if (data.ok) { showFormDialog.value = false; await loadElements(); }
      else ElMessage.error(data.error || "更新失败");
    } else {
      const { data } = await apiCreateWebElement(form.value);
      if (data.ok) { showFormDialog.value = false; await loadElements(); }
      else ElMessage.error(data.error || "创建失败");
    }
  } catch (e) { ElMessage.error(e?.response?.data?.error || "操作失败"); }
}

// ── Batch import ──
const showBatchDialog = ref(false);
const batchJson = ref("");
function openBatch() { batchJson.value = ""; showBatchDialog.value = true; }
async function doBatchImport() {
  const raw = batchJson.value.trim();
  if (!raw) { ElMessage.warning("请输入 JSON 数据"); return; }
  let items;
  try { items = JSON.parse(raw); } catch { ElMessage.error("JSON 格式无效"); return; }
  if (!Array.isArray(items) || !items.length) { ElMessage.warning("请输入有效的 JSON 数组"); return; }
  try {
    const { data } = await apiBatchImportWebElements(items);
    if (data.ok) {
      ElMessage.success(`成功导入 ${data.saved} 个元素${data.skipped ? `，跳过 ${data.skipped} 个` : ""}`);
      showBatchDialog.value = false;
      await loadElements();
    } else ElMessage.error(data.error || "导入失败");
  } catch (e) { ElMessage.error("导入失败"); }
}
</script>

<template>
  <div class="web-element-manager">
    <div class="main-layout">
      <!-- Left: Group Tree -->
      <aside class="tree-panel">
        <div v-if="!selectMode" class="tree-header">
          <span class="tree-header__title">项目分组</span>
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
                <span v-if="data.element_count" class="tree-node__meta">{{ data.element_count }} 元素</span>
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

      <!-- Right: Element table -->
      <template v-if="selectedGroup">
        <div class="elements-panel">
          <div class="panel-header">
            <h3 class="panel-title">
              {{ groupLabel(selectedGroup) }}
              <span class="doc-tag">Web Elements</span>
            </h3>
            <div class="panel-header__actions">
              <el-button size="small" @click="openBatch">📥 批量导入</el-button>
              <el-button size="small" type="primary" @click="openAdd">+ 添加元素</el-button>
            </div>
          </div>
          <div class="elements-subheader">
            <AppTabs class="element-tabs" :items="filterTabs" v-model="filterMode" :leaf-animation="true" :shadow="true">
              <template v-for="tab in filterTabs" :key="tab.key" #[tab.key]>
                <div class="table-area">
                  <div class="table-toolbar">
                    <div class="page-size-control">
                      <span class="toolbar-label">显示行数</span>
                      <div class="page-size-btns">
                        <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" type="button" class="page-size-btn"
                          :class="{ active: pageSize === n }" @click="setPageSize(n)">{{ n }}</button>
                      </div>
                    </div>
                    <div v-if="filteredElements.length > 0" class="table-toolbar-right">
                      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredElements.length }} 条</span>
                      <div v-if="totalPages > 1" class="page-nav">
                        <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                        <el-button size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                      </div>
                    </div>
                  </div>
                  <AppCard class="table-card">
                    <div class="table-scroll">
                      <AppTable :columns="columns" :data-source="pagedElements" row-key="id" :striped="true" :loading="loading"
                        empty-text="暂无 Web 元素" class="web-elements-table">
                        <template #cell-name="{ record }">
                          <input class="cell-input" :value="record.name" placeholder="未命名"
                            @blur="(e) => updateEl(record, 'name', e.target.value)"
                            @keyup.enter="(e) => { updateEl(record, 'name', e.target.value); e.target.blur() }" />
                        </template>
                        <template #cell-locator_type="{ value }">
                          <span :class="['locator-tag', 'locator-tag--' + value]">{{ LOCATOR_LABEL_MAP[value] || value }}</span>
                        </template>
                        <template #cell-locator_value="{ record }">
                          <span class="cell-code" :title="record.locator_value">{{ record.locator_value }}</span>
                        </template>
                        <template #cell-page_url="{ value }">
                          <span v-if="value" class="cell-url" :title="value">{{ value }}</span>
                          <span v-else class="text-muted">—</span>
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
                          <div class="table-empty"><span>🌐</span><p>暂无 Web 元素</p>
                            <el-button size="small" type="primary" @click="openAdd">添加第一个元素</el-button></div>
                        </template>
                      </AppTable>
                    </div>
                  </AppCard>
                </div>
              </template>
            </AppTabs>
            <span class="element-count">共 {{ elements.length }} 个元素</span>

            <!-- Page Flows Section -->
            <div v-if="selectedGroup && selectedGroup.id !== '__ungrouped__'" class="flows-section">
              <div class="flows-header">
                <span class="flows-title">页面跳转流 ({{ flows.length }})</span>
                <el-button size="small" @click="openAddFlow">+ 添加跳转</el-button>
              </div>
              <div v-if="flows.length" class="flows-list">
                <div v-for="f in flows" :key="f.id" class="flow-item" :class="{ 'flow-outgoing': f.from_group_id === selectedGroup.id, 'flow-incoming': f.to_group_id === selectedGroup.id }">
                  <span class="flow-dir-tag">{{ f.from_group_id === selectedGroup.id ? '发出' : '流入' }}</span>
                  <span class="flow-arrow">
                    <span class="flow-label" :class="{ 'flow-from': f.from_group_id === selectedGroup.id }">{{ f.from_label }}</span>
                    <span class="flow-arrow-icon">→</span>
                    <span class="flow-label" :class="{ 'flow-to': f.to_group_id === selectedGroup.id }">{{ f.to_label }}</span>
                  </span>
                  <span class="flow-meta">
                    <code>{{ f.trigger_action }}</code>
                    <span v-if="f.trigger_name" class="flow-trigger">{{ f.trigger_name }}</span>
                  </span>
                  <el-button size="small" type="danger" link @click="doDeleteFlow(f)">断开</el-button>
                </div>
              </div>
              <div v-else class="flows-empty">暂无跳转关系</div>
            </div>
          </div>
        </div>
      </template>
      <AppCard v-else class="empty-card">
        <div class="empty-state">← 选择左侧分组查看元素</div>
      </AppCard>
    </div>

    <!-- Add/Edit dialog -->
    <el-dialog v-model="showFormDialog" :title="formTitle" width="520px" :close-on-click-modal="false" @close="showFormDialog = false">
      <div class="form-grid">
        <label class="form-label required">元素名称</label>
        <el-input v-model="form.name" placeholder="如：登录按钮" size="middle" />
        <label class="form-label">所属分组</label>
        <el-select v-model="form.group_id" placeholder="选择分组（可选）" clearable style="width: 100%" size="middle">
          <el-option v-for="g in groups.filter(x => !x.is_folder)" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <label class="form-label required">定位方式</label>
        <el-select v-model="form.locator_type" style="width: 100%" size="middle">
          <el-option v-for="t in LOCATOR_TYPES" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <label class="form-label required">定位值</label>
        <el-input v-model="form.locator_value" :placeholder="selectedLocator.hint" size="middle" />
        <label class="form-label">页面 URL</label>
        <el-input v-model="form.page_url" placeholder="https://example.com/login" size="middle" />
        <label class="form-label">描述</label>
        <el-input v-model="form.description" placeholder="元素用途说明" size="middle" />
        <label class="form-label">标签</label>
        <el-input v-model="form.tags" placeholder="逗号分隔" size="middle" />
        <label class="form-label">测试点</label>
        <el-switch v-model="form.is_test_point" size="medium" />
      </div>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="doSave">{{ editingId ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- Batch Import -->
    <el-dialog v-model="showBatchDialog" title="批量导入 Web 元素" width="600px" :close-on-click-modal="false">
      <div class="form-grid">
        <label class="form-label">JSON 数据</label>
        <el-input v-model="batchJson" type="textarea" :rows="12"
          placeholder='[{"name":"登录按钮","locator_type":"css_selector","locator_value":".login-btn","page_url":"https://..."}]' />
      </div>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="doBatchImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- Create Group -->
    <el-dialog v-model="showCreateGroup" :title="createIsFolder ? '新建项目目录' : '新建模块'" width="360px" :close-on-click-modal="false">
      <div class="form-grid">
        <label class="form-label required">名称</label>
        <el-input v-model="newGroupForm.name" :placeholder="createIsFolder ? '如：电商项目' : '如：登录模块'" size="middle"
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

    <!-- Add Flow Dialog -->
    <el-dialog v-model="showFlowDialog" title="添加页面跳转" width="480px" :close-on-click-modal="false" @close="showFlowDialog = false">
      <div class="form-grid">
        <label class="form-label required">源页面</label>
        <el-select v-model="newFlowForm.from_group_id" placeholder="选择源页面" style="width:100%" size="middle" :disabled="!!selectedGroup">
          <el-option v-for="g in groups.filter(x => !x.is_folder)" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <label class="form-label required">目标页面</label>
        <el-select v-model="newFlowForm.to_group_id" placeholder="选择目标页面" style="width:100%" size="middle">
          <el-option v-for="g in groups.filter(x => !x.is_folder && g.id !== newFlowForm.from_group_id)" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <label class="form-label">触发元素</label>
        <el-select v-model="newFlowForm.trigger_element_id" placeholder="选择触发元素（可选）" clearable style="width:100%" size="middle">
          <el-option v-for="el in elements" :key="el.id" :label="el.name" :value="el.id" />
        </el-select>
        <label class="form-label">动作类型</label>
        <el-select v-model="newFlowForm.trigger_action" style="width:100%" size="middle">
          <el-option label="click" value="click" />
          <el-option label="navigate" value="navigate" />
          <el-option label="submit" value="submit" />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="showFlowDialog = false">取消</el-button>
        <el-button type="primary" @click="doCreateFlow">创建</el-button>
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
.web-element-manager {
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
.tree-panel {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(139, 115, 85, 0.16);
  border-radius: 12px;
  overflow: hidden;
  min-height: 0;
}

.tree-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.1);
  background: rgba(139, 115, 85, 0.04);
  flex-shrink: 0;
}

.tree-header--select {
  background: rgba(25, 200, 185, 0.08);
}

.tree-header__title {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
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
  color: #9f927d;
  font-size: 13px;
}

.tree-empty__icon {
  display: block;
  font-size: 32px;
  margin-bottom: 8px;
}

.tree-empty__text {
  font-weight: 600;
  color: #6b5b48;
  margin: 0 0 4px;
}

.tree-empty__hint {
  font-size: 12px;
  color: #9f927d;
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
  color: #4a3a28;
}

.tree-node--folder .tree-node__name {
  font-weight: 600;
  color: #6b5b48;
}

.tree-node--active .tree-node__name {
  color: #0f8b7e;
  font-weight: 700;
}

.tree-node__meta {
  font-size: 11px;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.06);
  padding: 1px 6px;
  border-radius: 8px;
  flex-shrink: 0;
}

.ungrouped-node {
  padding: 6px 14px;
  margin-top: 4px;
  border-top: 1px dashed rgba(139, 115, 85, 0.12);
  cursor: pointer;
  border-radius: 6px;
}

.ungrouped-node:hover {
  background: rgba(139, 115, 85, 0.06);
}

.ungrouped-node.tree-node--active {
  background: rgba(25, 200, 185, 0.12);
}

/* ── Context Menu ── */
.context-menu {
  position: fixed;
  z-index: 3000;
  background: #fff;
  border: 1px solid rgba(139, 115, 85, 0.16);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  min-width: 140px;
  padding: 4px 0;
}

.context-menu__item {
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
  color: #4a3a28;
}

.context-menu__item:hover {
  background: rgba(139, 115, 85, 0.06);
}

.context-menu__item--danger {
  color: #e05a5a;
}

.context-menu__divider {
  height: 1px;
  background: rgba(139, 115, 85, 0.1);
  margin: 4px 8px;
}

/* ── Elements Panel ── */
.elements-panel {
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

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #4A3A28;
  margin: 0;
}

.doc-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  background: rgba(139, 115, 85, 0.1);
  color: #8b7355;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  vertical-align: middle;
}

.elements-subheader {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.element-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.element-count {
  font-size: 12px;
  color: #8a7b66;
  text-align: right;
  flex-shrink: 0;
}

.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
}

.empty-state {
  font-size: 14px;
  color: #9f927d;
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
  color: #8a7b66;
}

.page-size-btns {
  display: flex;
  gap: 6px;
}

.page-size-btn {
  min-width: 40px;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(139, 115, 85, 0.2);
  background: #f7f3df;
  font-size: 12px;
  font-weight: 600;
  color: #6b5b48;
  cursor: pointer;
  transition: all 0.2s;
}

.page-size-btn:hover {
  border-color: #19c8b9;
  color: #19c8b9;
}

.page-size-btn.active {
  background: rgba(25, 200, 185, 0.12);
  border-color: #19c8b9;
  color: #19c8b9;
}

.table-toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.page-info {
  font-size: 12px;
  color: #8a7b66;
}

.page-nav {
  display: flex;
  gap: 8px;
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

/* ── Locator Tags ── */
.locator-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

.locator-tag--css_selector { background: #889df0; }
.locator-tag--xpath { background: #b39ef3; }
.locator-tag--id { background: #6fba2c; }
.locator-tag--class_name { background: #19c8b9; }
.locator-tag--name { background: #f7cd67; color: #5a4a20; }
.locator-tag--tag_name { background: #8b7355; }
.locator-tag--link_text { background: #e85f5f; }
.locator-tag--partial_link_text { background: #f8a6b2; color: #5a4a20; }
.locator-tag--text { background: #f7a8c4; }
.locator-tag--test_id { background: #c5db5a; color: #5a4a20; }
.locator-tag--role { background: #b6e663; color: #5a4a20; }
.locator-tag--placeholder { background: #f5c6a3; color: #5a4a20; }

/* ── Cell Styles ── */
.cell-input {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 13px;
  color: #19c8b9;
  font-weight: 600;
  padding: 4px 6px;
  border-radius: 4px;
  outline: none;
  transition: background 0.2s;
}

.cell-input:hover,
.cell-input:focus {
  background: rgba(25, 200, 185, 0.06);
}

.cell-input--desc {
  color: #4a3a28;
  font-weight: 400;
  font-size: 12px;
}

.cell-code {
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 12px;
  color: #8275c2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 250px;
}

.cell-url {
  font-size: 12px;
  color: #6b5b48;
  opacity: 0.7;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 160px;
}

.text-muted {
  color: #ccc;
  font-size: 11px;
  font-style: italic;
}

.action-btns {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* ── Empty ── */
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
  color: #9f927d;
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
  color: #988b7a;
  text-align: right;
}

.form-label.required::before {
  content: "*";
  color: #e8998a;
  margin-right: 2px;
}

/* ── Flows Section ── */
.flows-section {
  border-top: 1px dashed rgba(139,115,85,0.12);
  padding-top: 12px;
  margin-top: 8px;
  flex-shrink: 0;
}
.flows-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.flows-title {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
}
.flows-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.flow-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.6);
  border-radius: 10px;
  border: 1px solid rgba(139,115,85,0.08);
  font-size: 13px;
}
.flow-item.flow-outgoing { border-left: 3px solid #19c8b9; }
.flow-item.flow-incoming { border-left: 3px solid #889df0; }
.flow-dir-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 6px;
  flex-shrink: 0;
}
.flow-outgoing .flow-dir-tag { background: rgba(25,200,185,0.12); color: #19c8b9; }
.flow-incoming .flow-dir-tag { background: rgba(136,157,240,0.12); color: #889df0; }
.flow-arrow {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}
.flow-arrow-icon {
  color: #19c8b9;
  font-weight: 700;
}
.flow-label {
  font-weight: 600;
  color: #4a3a28;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.flow-label.flow-from { color: #19c8b9; }
.flow-label.flow-to { color: #889df0; }
.flow-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #9f927d;
}
.flow-meta code {
  background: #f0ebe0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.flow-trigger {
  color: #8275c2;
  font-weight: 500;
}
.flows-empty {
  text-align: center;
  color: #9f927d;
  font-size: 12px;
  padding: 12px 0;
}
</style>
