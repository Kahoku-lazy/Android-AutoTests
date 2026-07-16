<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import {
  ElMessage,
  ElMessageBox,
  ElTag,
} from "element-plus";
import { Button as AnimalButton, Card, Table } from "animal-island-vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import DirectoryTree from "./components/DirectoryTree.vue";
import CaseCard from "./components/CaseCard.vue";
import StepViewer from "./components/StepViewer.vue";
import {
  fetchDirectories,
  listDefinitions,
  deleteDefinition,
  getDefinition,
  exportYaml,
  listExports,
} from "./api.js";

const router = useRouter();
const caseLayoutRef = ref(null);

// ── State ──
const treeData = ref([]);
const definitions = ref([]);
const loading = ref(false);
const activeDirectoryId = ref(null);
const activeDirName = ref("");

// Detail view state
const selectedCase = ref(null);
const selectedCaseLoading = ref(false);

// YAML export state
const exportLoading = ref(false);
const exportFiles = ref([]);
const showExports = ref(false);

// View mode
const STORAGE_KEY = "case-manager-view-mode";
const viewMode = ref(localStorage.getItem(STORAGE_KEY) || "card");

// Sidebar resize
const SIDEBAR_WIDTH_KEY = "case-manager-sidebar-width";
const SIDEBAR_MIN = 220;
const SIDEBAR_MAX = 560;
const SIDEBAR_DEFAULT = 300;

function clampSidebarWidth(width) {
  return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, width));
}

const sidebarWidth = ref(
  clampSidebarWidth(Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || SIDEBAR_DEFAULT),
);
const isResizingSidebar = ref(false);

function onSidebarResizeStart(e) {
  if (e.button !== 0) return;
  e.preventDefault();
  isResizingSidebar.value = true;
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
}

function onSidebarResizeMove(e) {
  if (!isResizingSidebar.value || !caseLayoutRef.value) return;
  const rect = caseLayoutRef.value.getBoundingClientRect();
  sidebarWidth.value = clampSidebarWidth(e.clientX - rect.left);
}

function onSidebarResizeEnd() {
  if (!isResizingSidebar.value) return;
  isResizingSidebar.value = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value));
}

function resetSidebarWidth() {
  sidebarWidth.value = SIDEBAR_DEFAULT;
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(SIDEBAR_DEFAULT));
}

function setViewMode(mode) {
  viewMode.value = mode;
  localStorage.setItem(STORAGE_KEY, mode);
}

// ── Data loading ──
onMounted(async () => {
  window.addEventListener("mousemove", onSidebarResizeMove);
  window.addEventListener("mouseup", onSidebarResizeEnd);
  await loadDirectories();
  await loadDefs();
});

onUnmounted(() => {
  window.removeEventListener("mousemove", onSidebarResizeMove);
  window.removeEventListener("mouseup", onSidebarResizeEnd);
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
});

async function loadDirectories() {
  try {
    const { data } = await fetchDirectories();
    if (data.ok) treeData.value = data.tree;
  } catch (_) {}
}

async function loadDefs() {
  loading.value = true;
  try {
    const { data } = await listDefinitions(activeDirectoryId.value);
    if (data.ok) definitions.value = data.definitions;
  } catch (_) {}
  loading.value = false;
}

// ── Directory / Case selection ──
function handleDirSelect(node) {
  if (node.node_type === "case") {
    loadCaseDetail(node.case_id);
  } else {
    selectedCase.value = null;
    activeDirectoryId.value = node.id;
    activeDirName.value = node.name;
    loadDefs();
  }
}

function handleDirRefresh() {
  loadDirectories();
  loadDefs(); // B7修复: 树删除后同步右侧列表
  // E2修复: 删除用例后清空详情面板
  if (selectedCase.value) {
    const stillExists = definitions.value.some(d => d.id === selectedCase.value.id);
    if (!stillExists) selectedCase.value = null;
  }
}

// ── Case detail ──
async function loadCaseDetail(caseId) {
  selectedCaseLoading.value = true;
  try {
    const { data } = await getDefinition(caseId);
    if (data.ok) selectedCase.value = data.definition;
  } catch (_) {}
  selectedCaseLoading.value = false;
}

function handleBackToList() {
  selectedCase.value = null;
}

// ── YAML Export ──
async function doExportYaml() {
  exportLoading.value = true;
  try {
    const { data } = await exportYaml();
    if (data.ok) {
      ElMessage.success(`YAML 已导出：${data.filename}`);
      await loadExportFiles();
      showExports.value = true;
    } else {
      ElMessage.error(data.error || "导出失败");
    }
  } catch (_) {
    ElMessage.error("导出失败，请检查网络后重试");
  }
  exportLoading.value = false;
}

async function loadExportFiles() {
  try {
    const { data } = await listExports();
    if (data.ok) exportFiles.value = data.files;
  } catch (_) {}
}

function downloadExportFile(filename) {
  window.open(`/api/cases/exports/${filename}`, "_blank");
}

// ── Breadcrumb path ──
const allActive = computed(() => activeDirectoryId.value === null);

function goToAll() {
  activeDirectoryId.value = null;
  activeDirName.value = "";
  loadDefs();
}

const breadcrumbPath = computed(() => {
  const parts = [];
  if (activeDirectoryId.value) {
    function find(node, id) {
      if (node.id === id) return [node];
      if (node.children) {
        for (const child of node.children) {
          const found = find(child, id);
          if (found) return [node, ...found];
        }
      }
      return null;
    }
    for (const root of treeData.value) {
      const found = find(root, activeDirectoryId.value);
      if (found) {
        parts.push(...found);
        break;
      }
    }
    if (parts.length === 0 && activeDirName.value) {
      parts.push({
        id: activeDirectoryId.value,
        name: activeDirName.value,
        parent_id: 1,
      });
    }
  }
  return parts;
});

// ── Table columns ──
const columns = [
  { title: "ID", dataIndex: "id", width: "18%" },
  { title: "标题", dataIndex: "title", width: "28%" },
  { title: "目录", dataIndex: "directory_name", width: "12%" },
  { title: "分类", dataIndex: "category", width: "12%" },
  { title: "启用", dataIndex: "enabled", width: "8%", align: "center" },
  { title: "操作", dataIndex: "actions", width: "22%", align: "center" },
];

// ── Actions ──
function create() {
  const query = activeDirectoryId.value
    ? { directory_id: activeDirectoryId.value }
    : {};
  router.push({ path: "/cases/new", query });
}

function edit(row) {
  router.push(`/cases/${row.id}/edit`);
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除用例「${row.title}」？`, "确认删除", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch (_) {
    return; // 用户取消
  }
  try {
    await deleteDefinition(row.id);
    ElMessage.success("已删除");
    loadDefs();
    loadDirectories();
    // E2修复: 删除后清空详情
    if (selectedCase.value?.id === row.id) selectedCase.value = null;
  } catch (e) {
    ElMessage.error("删除失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
  }
}
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="测试用例 Test Cases"
      subtitle="管理自动化测试用例工程，支持目录层级、分类与双视图浏览"
      color="app-yellow"
    />

    <div ref="caseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
      <!-- Left: Directory Tree -->
      <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
        <DirectoryTree
          :tree-data="treeData"
          :active-id="activeDirectoryId"
          @select="handleDirSelect"
          @refresh="handleDirRefresh"
        />
      </aside>

      <!-- Resize handle -->
      <div
        class="case-sidebar-resizer"
        :class="{ 'is-dragging': isResizingSidebar }"
        title="拖动调整宽度，双击恢复默认"
        @mousedown="onSidebarResizeStart"
        @dblclick="resetSidebarWidth"
      />

      <!-- Right: Content -->
      <main class="case-main">
        <!-- Toolbar -->
        <div class="case-toolbar">
          <div class="case-toolbar__left">
            <nav class="case-breadcrumb" aria-label="用例导航">
              <button
                type="button"
                class="crumb crumb--root"
                :class="{ 'crumb--active': allActive && !selectedCase }"
                @click="goToAll"
              >
                <span class="crumb__icon" aria-hidden="true">📋</span>
                <span class="crumb__label">全部用例</span>
              </button>

              <template v-for="node in breadcrumbPath" :key="node.id">
                <span class="crumb-sep" aria-hidden="true">›</span>
                <span class="crumb crumb--active crumb--dir">
                  <span class="crumb__icon" aria-hidden="true">{{
                    node.parent_id === null ? "📁" : "📂"
                  }}</span>
                  <span class="crumb__label">{{ node.name }}</span>
                </span>
              </template>

              <template v-if="selectedCase">
                <span class="crumb-sep" aria-hidden="true">›</span>
                <span class="crumb crumb--active crumb--case">
                  <span class="crumb__icon" aria-hidden="true">📄</span>
                  <span class="crumb__label">{{
                    selectedCase.title || "未命名用例"
                  }}</span>
                </span>
              </template>
            </nav>

            <span class="case-count-badge">
              <span class="case-count-badge__num">{{ definitions.length }}</span>
              <span class="case-count-badge__text">个用例</span>
            </span>
          </div>
          <div class="case-toolbar__right">
            <div class="view-toggle">
              <button
                class="view-btn"
                :class="{ 'view-btn--active': viewMode === 'list' }"
                @click="setViewMode('list')"
                title="列表视图"
              >
                📋
              </button>
              <button
                class="view-btn"
                :class="{ 'view-btn--active': viewMode === 'card' }"
                @click="setViewMode('card')"
                title="卡片视图"
              >
                🃏
              </button>
            </div>
            <AnimalButton
              type="primary"
              :loading="exportLoading"
              @click="doExportYaml"
              >📤 导出 YAML</AnimalButton
            >
            <AnimalButton type="primary" @click="create"
              >+ 新建用例</AnimalButton
            >
          </div>
        </div>

        <!-- === Detail View === -->
        <div v-if="selectedCase" class="case-detail">
          <div class="case-detail__toolbar">
            <AnimalButton size="small" @click="handleBackToList"
              >↩ 返回列表</AnimalButton
            >
            <AnimalButton
              size="small"
              type="primary"
              @click="edit(selectedCase)"
              >📝 编辑用例</AnimalButton
            >
          </div>

          <Card color="app-teal" pattern="app-teal" class="case-detail__header">
            <div class="case-detail__head-row">
              <span class="case-detail__id">{{ selectedCase.id }}</span>
              <el-tag
                :type="selectedCase.enabled ? 'success' : 'info'"
                effect="dark"
                size="small"
                round
              >
                {{ selectedCase.enabled ? "启用" : "停用" }}
              </el-tag>
              <span
                class="case-detail__priority"
                :class="
                  'case-detail__priority--' +
                  (selectedCase.priority || 'P1').toLowerCase()
                "
              >
                {{ selectedCase.priority }}
              </span>
            </div>
            <h2 class="case-detail__title">
              {{ selectedCase.title || "未命名用例" }}
            </h2>
            <div class="case-detail__meta">
              <span
                v-if="selectedCase.category"
                class="case-detail__meta-tag"
                >{{ selectedCase.category }}</span
              >
              <span
                v-if="selectedCase.directory_name"
                class="case-detail__meta-tag case-detail__meta-tag--dir"
                >{{ selectedCase.directory_name }}</span
              >
              <span class="case-detail__meta-tag">{{
                selectedCase.package_name
              }}</span>
              <span class="case-detail__meta-tag"
                >{{ (selectedCase.steps_data || []).length }} 步骤</span
              >
            </div>
            <div v-if="selectedCase.description" class="case-detail__desc">
              {{ selectedCase.description }}
            </div>
          </Card>

          <div class="case-detail__steps">
            <h3 class="case-detail__steps-title">
              📋 测试步骤 ({{ (selectedCase.steps_data || []).length }})
            </h3>
            <Card color="brown" pattern="brown">
              <StepViewer :steps="selectedCase.steps_data || []" />
            </Card>
          </div>
        </div>

        <!-- === List View === -->
        <div v-else class="case-content">
          <!-- Card Grid -->
          <div v-if="viewMode === 'card'" class="card-grid">
            <template v-if="definitions.length > 0">
              <CaseCard
                v-for="item in definitions"
                :key="item.id"
                :item="item"
                @edit="edit"
                @delete="remove"
                @select="loadCaseDetail(item.id)"
              />
            </template>
            <div v-else class="card-grid-empty">
              <span>📋</span>
              <p>{{ allActive ? "暂无用例定义" : "此目录下暂无用例" }}</p>
              <AnimalButton size="small" type="primary" @click="create">创建第一个用例</AnimalButton>
            </div>
          </div>

          <!-- Table -->
          <Card v-else color="brown" pattern="brown" class="table-card">
            <Table
              :columns="columns"
              :data-source="definitions"
              row-key="id"
              :striped="false"
              :loading="loading"
              empty-text="暂无用例定义"
              class="case-table case-table--rainbow"
            >
              <template #cell-id="{ record }">
                <code class="cell-id">{{ record.id }}</code>
              </template>
              <template #cell-title="{ record }">
                <span class="cell-title">{{ record.title || "未命名用例" }}</span>
              </template>
              <template #cell-enabled="{ value }">
                <el-tag
                  :type="value ? 'success' : 'info'"
                  effect="dark"
                  size="small"
                  round
                >
                  {{ value ? "启用" : "停用" }}
                </el-tag>
              </template>
              <template #cell-directory_name="{ value }">
                <span v-if="value" class="cell-dir">{{ value }}</span>
                <span v-else class="cell-dir cell-dir--none">—</span>
              </template>
              <template #cell-category="{ value }">
                <span class="cell-category">{{ value || "—" }}</span>
              </template>
              <template #cell-actions="{ record }">
                <div class="action-cell">
                  <button
                    type="button"
                    class="act-btn act-btn--view"
                    title="查看详情"
                    @click="loadCaseDetail(record.id)"
                  >查看</button>
                  <button
                    type="button"
                    class="act-btn act-btn--edit"
                    title="编辑用例"
                    @click="edit(record)"
                  >编辑</button>
                  <button
                    type="button"
                    class="act-btn act-btn--del"
                    title="删除用例"
                    @click="remove(record)"
                  >删除</button>
                </div>
              </template>
              <template #empty>
                <div class="table-empty">
                  <span>📋</span>
                  <p>{{ allActive ? "暂无用例定义" : "此目录下暂无用例" }}</p>
                  <AnimalButton size="small" type="primary" @click="create"
                    >创建第一个用例</AnimalButton
                  >
                </div>
              </template>
            </Table>
          </Card>
        </div>

        <!-- YAML Export file list -->
        <div v-if="showExports" class="case-exports">
          <div class="case-exports__header">
            <h3 class="case-exports__title">📤 导出文件</h3>
            <AnimalButton size="small" @click="showExports = false"
              >✕ 收起</AnimalButton
            >
          </div>
          <Card color="brown" pattern="brown" class="case-exports__table">
            <div v-if="exportFiles.length === 0" class="case-exports__empty">
              暂无导出文件
            </div>
            <table v-else class="exports-table">
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>大小</th>
                  <th>时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="file in exportFiles" :key="file.name">
                  <td class="exports-table__name">{{ file.name }}</td>
                  <td>{{ (file.size / 1024).toFixed(1) }} KB</td>
                  <td>{{ file.time }}</td>
                  <td>
                    <AnimalButton
                      size="small"
                      type="primary"
                      @click="downloadExportFile(file.name)"
                      >⬇ 下载</AnimalButton
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </Card>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── Page scroll ── */
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── Layout ── */
.case-layout {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: row;
  gap: 0;
  padding: 0;
  max-width: none;
  width: 100%;
  margin: 0;
  overflow: hidden;
}

.case-layout--resizing {
  cursor: col-resize;
  user-select: none;
}

.case-sidebar {
  flex-shrink: 0;
  align-self: stretch;
  min-height: 0;
  min-width: 0;
  background: rgb(247, 243, 223);
  border-right: none;
  border-radius: 18px 0 0 18px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.case-sidebar-resizer {
  flex-shrink: 0;
  width: 6px;
  margin: 0 -3px;
  cursor: col-resize;
  position: relative;
  z-index: 2;
  align-self: stretch;
  transition: background 0.15s ease;
}

.case-sidebar-resizer::before {
  content: "";
  position: absolute;
  top: 12px;
  bottom: 12px;
  left: 50%;
  width: 2px;
  transform: translateX(-50%);
  border-radius: 2px;
  background: rgba(196, 184, 158, 0.45);
  transition: background 0.15s ease, width 0.15s ease;
}

.case-sidebar-resizer:hover::before,
.case-sidebar-resizer.is-dragging::before {
  width: 3px;
  background: #19c8b9;
}

.case-sidebar-resizer:hover,
.case-sidebar-resizer.is-dragging {
  background: rgba(25, 200, 185, 0.08);
}

.case-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 20px 0 12px;
  overflow-x: hidden;
  overflow-y: auto;
}

/* ── Toolbar ── */
.case-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
  background: rgb(247, 243, 223);
  border: 2px solid #c4b89e;
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(61, 52, 40, 0.07);
  flex-shrink: 0;
}

.case-toolbar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  min-width: 0;
  flex: 1;
}

.case-toolbar__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* Breadcrumb — animal-island app-teal 风格 */
.case-breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.crumb {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 6px 12px;
  border-radius: 50px;
  border: 1.5px solid transparent;
  background: rgba(255, 255, 255, 0.45);
  color: #794f27;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
  transition: all 0.15s ease;
}

.crumb--root {
  cursor: pointer;
  font-family: var(--font-display, Nunito, sans-serif);
}

.crumb--root:not(.crumb--active):hover {
  background: rgba(25, 200, 185, 0.12);
  border-color: rgba(25, 200, 185, 0.4);
  color: #0d6e64;
}

.crumb--active {
  background: #ddf3ea;
  border-color: #19c8b9;
  color: #0a5c52;
  font-weight: 700;
  box-shadow: 0 1px 4px rgba(25, 200, 185, 0.18);
}

.crumb--case .crumb__label {
  font-style: italic;
}

.crumb__icon {
  flex-shrink: 0;
  font-size: 14px;
  line-height: 1;
}

.crumb__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.crumb-sep {
  color: #b8a898;
  font-weight: 700;
  font-size: 15px;
  line-height: 1;
  user-select: none;
  padding: 0 2px;
}

.case-count-badge {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 50px;
  background: rgba(25, 200, 185, 0.14);
  border: 1.5px solid rgba(25, 200, 185, 0.38);
  white-space: nowrap;
  flex-shrink: 0;
}

.case-count-badge__num {
  font-size: 15px;
  font-weight: 800;
  color: #0a5c52;
  font-family: var(--font-display, Nunito, sans-serif);
  line-height: 1;
}

.case-count-badge__text {
  font-size: 12px;
  font-weight: 600;
  color: #3d7a72;
}

/* View toggle */
.view-toggle {
  display: flex;
  background: rgba(255, 255, 255, 0.55);
  border: 1.5px solid rgba(196, 184, 158, 0.55);
  border-radius: 12px;
  padding: 3px;
}
.view-btn {
  width: 36px;
  height: 32px;
  border: none;
  border-radius: 9px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8a7b66;
  transition: all 0.15s ease;
}
.view-btn:hover {
  background: rgba(25, 200, 185, 0.1);
  color: #0d6e64;
}
.view-btn--active {
  background: #19c8b9;
  color: #fff;
  box-shadow: 0 2px 6px rgba(25, 200, 185, 0.35);
}

/* Card Grid */
.case-content {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.card-grid-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 24px;
  color: #988b7a;
  text-align: center;
}
.card-grid-empty span {
  font-size: 48px;
}
.card-grid-empty p {
  font-size: 15px;
  margin: 0;
  font-weight: 600;
}

/* Table — 彩虹渐变列（Card 无 __content 层，padding 需直接覆写根节点） */
.table-card {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: visible;
  border-radius: 16px;
  padding: 0;
  cursor: default;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  width: 100%;
}
.case-table {
  width: 100%;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.case-table :deep(.animal-table-wrapper) {
  width: 100%;
  overflow: visible !important;
  max-height: none !important;
}
.case-table :deep(table) {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

/* 表头：每列独立彩虹渐变 */
.case-table--rainbow :deep(th) {
  font-size: 18px;
  font-weight: 800;
  padding: 16px 12px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  border: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.case-table--rainbow :deep(th:nth-child(1)) {
  background: linear-gradient(135deg, #f8a6b2 0%, #e85f5f 100%);
  color: #fff;
}
.case-table--rainbow :deep(th:nth-child(2)) {
  background: linear-gradient(135deg, #ffd97a 0%, #f7cd67 45%, #f5a623 100%);
  color: #5c3d10;
}
.case-table--rainbow :deep(th:nth-child(3)) {
  background: linear-gradient(135deg, #c5db5a 0%, #6fba2c 100%);
  color: #2d5016;
}
.case-table--rainbow :deep(th:nth-child(4)) {
  background: linear-gradient(135deg, #7ee8df 0%, #19c8b9 100%);
  color: #064a44;
}
.case-table--rainbow :deep(th:nth-child(5)) {
  background: linear-gradient(135deg, #a8b8ff 0%, #889df0 100%);
  color: #2a3568;
}
.case-table--rainbow :deep(th:nth-child(6)) {
  background: linear-gradient(135deg, #d4c4ff 0%, #b39ef3 100%);
  color: #3d2d6b;
  text-align: center;
}

/* 数据行：中性背景，字体按列着色 */
.case-table--rainbow :deep(td) {
  padding: 13px 12px;
  font-size: 14px;
  color: #4a3a28;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(139, 115, 85, 0.08);
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
}
.case-table--rainbow :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.03);
}
.case-table--rainbow :deep(tr:hover td) {
  background: rgba(25, 200, 185, 0.06);
}
.case-table--rainbow :deep(tr:last-child td) {
  border-bottom: none;
}
.case-table--rainbow :deep(td:nth-child(6)) {
  text-align: center;
  overflow: visible;
}

/* 操作按钮 — 紧凑 + 颜色区分 */
.action-cell {
  display: inline-flex;
  gap: 3px;
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.act-btn {
  padding: 3px 8px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  border-radius: 6px;
  border: 1.5px solid;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
  font-family: inherit;
}
.act-btn--view {
  color: #0a5c52;
  background: rgba(25, 200, 185, 0.14);
  border-color: rgba(25, 200, 185, 0.5);
}
.act-btn--view:hover {
  background: #19c8b9;
  border-color: #19c8b9;
  color: #fff;
}
.act-btn--edit {
  color: #2a3568;
  background: rgba(136, 157, 240, 0.14);
  border-color: rgba(136, 157, 240, 0.5);
}
.act-btn--edit:hover {
  background: #889df0;
  border-color: #889df0;
  color: #fff;
}
.act-btn--del {
  color: #b83232;
  background: rgba(232, 95, 95, 0.1);
  border-color: rgba(232, 95, 95, 0.45);
}
.act-btn--del:hover {
  background: #e85f5f;
  border-color: #e85f5f;
  color: #fff;
}
.cell-id {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 14px;
  font-weight: 600;
  color: #c0392b;
  word-break: break-all;
  line-height: 1.45;
}
.cell-title {
  font-weight: 700;
  font-size: 14px;
  color: #b8860b;
  line-height: 1.45;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-dir {
  font-size: 14px;
  font-weight: 600;
  color: #4a8c1c;
}
.cell-dir--none {
  color: #b8a898;
  font-weight: 500;
}
.cell-category {
  font-size: 14px;
  font-weight: 600;
  color: #0d8a7f;
}

.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #988b7a;
}
.table-empty span {
  font-size: 36px;
}
.table-empty p {
  font-size: 15px;
  margin: 0;
}

/* ── Detail View ── */
.case-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.case-detail__toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 4px;
}

.case-detail__header {
  padding: 20px 24px;
}

.case-detail__head-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.case-detail__id {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 12px;
  font-weight: 600;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.06);
  padding: 3px 10px;
  border-radius: 8px;
}

.case-detail__title {
  font-family: Nunito, "Noto Sans SC", sans-serif;
  font-weight: 800;
  font-size: 22px;
  color: #4a3a28;
  margin: 0 0 12px;
}

.case-detail__priority {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
}
.case-detail__priority--p0 {
  background: rgba(224, 90, 90, 0.12);
  color: #c0392b;
}
.case-detail__priority--p1 {
  background: rgba(245, 195, 28, 0.15);
  color: #8b6914;
}
.case-detail__priority--p2 {
  background: rgba(139, 115, 85, 0.08);
  color: #9f927d;
}

.case-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.case-detail__meta-tag {
  font-size: 12px;
  font-weight: 600;
  color: #8a7b66;
  background: rgba(139, 115, 85, 0.06);
  padding: 3px 10px;
  border-radius: 8px;
}
.case-detail__meta-tag--dir {
  color: #11a89b;
  background: rgba(25, 200, 185, 0.08);
}

.case-detail__desc {
  margin-top: 12px;
  font-size: 14px;
  color: #725d42;
  line-height: 1.6;
  padding-top: 12px;
  border-top: 1px solid rgba(196, 184, 158, 0.3);
}

.case-detail__steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-detail__steps-title {
  font-family: Nunito, sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #6b5b48;
  margin: 0;
}

/* ── YAML Export ── */
.case-exports {
  margin-top: 24px;
}
.case-exports__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.case-exports__title {
  font-family: Nunito, sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #6b5b48;
  margin: 0;
}
.case-exports__table {
  overflow: hidden;
}
.case-exports__table {
  padding: 0;
}
.case-exports__empty {
  text-align: center;
  padding: 32px;
  color: #9f927d;
  font-size: 14px;
}
.exports-table {
  width: 100%;
  border-collapse: collapse;
}
.exports-table th {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
  padding: 14px 16px;
  text-align: left;
  background: rgba(139, 115, 85, 0.06);
  border-bottom: 2px solid rgba(139, 115, 85, 0.12);
}
.exports-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #4a3a28;
  border-bottom: 1px solid rgba(139, 115, 85, 0.06);
}
.exports-table tr:hover td {
  background: rgba(139, 115, 85, 0.03);
}
.exports-table__name {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 13px;
  color: #11a89b;
  font-weight: 600;
}
</style>
