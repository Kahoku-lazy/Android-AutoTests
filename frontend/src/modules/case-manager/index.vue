<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  ElMessage,
  ElMessageBox,
  ElTag,
  ElBreadcrumb,
  ElBreadcrumbItem,
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

function setViewMode(mode) {
  viewMode.value = mode;
  localStorage.setItem(STORAGE_KEY, mode);
}

// ── Data loading ──
onMounted(async () => {
  await loadDirectories();
  await loadDefs();
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
  { title: "ID", dataIndex: "id", width: "200px" },
  { title: "标题", dataIndex: "title" },
  { title: "目录", dataIndex: "directory_name", width: "140px" },
  { title: "分类", dataIndex: "category", width: "100px" },
  { title: "启用", dataIndex: "enabled", width: "80px", align: "center" },
  { title: "操作", dataIndex: "actions", width: "200px", align: "center" },
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

    <div class="doc-body case-layout">
      <!-- Left: Directory Tree -->
      <aside class="case-sidebar">
        <DirectoryTree
          :tree-data="treeData"
          :active-id="activeDirectoryId"
          @select="handleDirSelect"
          @refresh="handleDirRefresh"
        />
      </aside>

      <!-- Right: Content -->
      <main class="case-main">
        <!-- Toolbar -->
        <div class="case-toolbar">
          <div class="case-toolbar__left">
            <el-breadcrumb separator="›">
              <el-breadcrumb-item>
                <span
                  class="breadcrumb-link"
                  :class="{ 'breadcrumb-active': allActive }"
                  @click="goToAll"
                >
                  📋 全部用例
                </span>
              </el-breadcrumb-item>
              <el-breadcrumb-item v-for="node in breadcrumbPath" :key="node.id">
                <span class="breadcrumb-link breadcrumb-active">
                  {{ node.parent_id === null ? "📁" : "📂" }} {{ node.name }}
                </span>
              </el-breadcrumb-item>
              <el-breadcrumb-item v-if="selectedCase">
                <span class="breadcrumb-link breadcrumb-active">
                  📄 {{ selectedCase.title || "未命名用例" }}
                </span>
              </el-breadcrumb-item>
            </el-breadcrumb>
            <span class="case-count">{{ definitions.length }} 个用例</span>
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
              :striped="true"
              :loading="loading"
              empty-text="暂无用例定义"
              class="case-table"
            >
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
                <span v-if="value" class="dir-cell">{{ value }}</span>
                <span v-else class="dir-cell dir-cell--none">—</span>
              </template>
              <template #cell-actions="{ record }">
                <div class="action-cell">
                  <AnimalButton
                    size="small"
                    type="primary"
                    @click="loadCaseDetail(record.id)"
                    >查看</AnimalButton
                  >
                  <AnimalButton
                    size="small"
                    type="primary"
                    @click="edit(record)"
                    >编辑</AnimalButton
                  >
                  <AnimalButton
                    size="small"
                    danger
                    plain
                    @click="remove(record)"
                    >删除</AnimalButton
                  >
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
/* ── Layout ── */
.case-layout {
  display: flex;
  flex-direction: row;
  gap: 0;
  padding: 0;
  max-width: 1320px;
  margin: 0 auto;
}

.case-sidebar {
  width: 260px;
  flex-shrink: 0;
  align-self: stretch;
  min-height: 400px;
  background: rgb(247, 243, 223);
  border-right: 2px solid rgba(196, 184, 158, 0.5);
  border-radius: 18px 0 0 18px;
  overflow: hidden;
}

.case-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 0 0 0 20px;
}

/* ── Toolbar ── */
.case-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 2px solid rgba(196, 184, 158, 0.3);
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.case-toolbar__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.case-toolbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.case-count {
  font-size: 13px;
  color: #9f927d;
  font-weight: 600;
}

/* Breadcrumb */
.breadcrumb-link {
  cursor: pointer;
  font-weight: 500;
  color: #9f927d;
  transition: color 0.15s ease;
}
.breadcrumb-link:hover {
  color: #19c8b9;
}
.breadcrumb-active {
  color: #6b5b48;
  font-weight: 700;
}

/* View toggle */
.view-toggle {
  display: flex;
  background: rgba(139, 115, 85, 0.06);
  border-radius: 10px;
  padding: 2px;
}
.view-btn {
  width: 36px;
  height: 32px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  color: #9f927d;
}
.view-btn:hover {
  color: #725d42;
}
.view-btn--active {
  background: #19c8b9;
  color: #fff;
  box-shadow: 0 2px 6px rgba(25, 200, 185, 0.3);
}

/* Card Grid */
.case-content {
  flex: 1;
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

/* Table */
.table-card {
  overflow: hidden;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
}
.case-table {
  width: 100%;
}
.case-table :deep(table) {
  width: 100%;
  border-collapse: collapse;
}
.case-table :deep(th) {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
  padding: 14px 16px;
  text-align: left;
  background: rgba(139, 115, 85, 0.06);
  border-bottom: 2px solid rgba(139, 115, 85, 0.12);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.case-table :deep(td) {
  padding: 12px 16px;
  font-size: 14px;
  color: #4a3a28;
  border-bottom: 1px solid rgba(139, 115, 85, 0.06);
  vertical-align: middle;
}
.case-table :deep(tr:hover td) {
  background: rgba(139, 115, 85, 0.03);
}
.case-table :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.02);
}
.case-table :deep(tr:nth-child(even):hover td) {
  background: rgba(139, 115, 85, 0.04);
}

.action-cell {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.dir-cell {
  font-size: 13px;
  color: #11a89b;
  font-weight: 600;
}
.dir-cell--none {
  color: #c4b89e;
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
.case-exports__table :deep(.animal-card__content) {
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
