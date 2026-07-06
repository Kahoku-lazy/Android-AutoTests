<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  ElMessage,
  ElMessageBox,
  ElTag,
  ElBreadcrumb,
  ElBreadcrumbItem,
} from "element-plus";
import { Button as AnimalButton, Card, Table, Tabs } from "animal-island-vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import DirectoryTree from "./components/DirectoryTree.vue";
import CaseCard from "./components/CaseCard.vue";
import { fetchDirectories, listDefinitions, deleteDefinition } from "./api.js";

const router = useRouter();
const route = useRoute();

// ── State ──
const treeData = ref([]);
const definitions = ref([]);
const loading = ref(false);
const activeDirectoryId = ref(null);
const activeDirName = ref("");

// View mode: 'list' | 'card', persisted in localStorage
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

// ── Directory selection ──
function handleDirSelect(node) {
  activeDirectoryId.value = node.id;
  activeDirName.value = node.name;
  loadDefs();
}

function handleDirRefresh() {
  loadDirectories();
}

// Watch for "all" navigation (clicking breadcrumb "全部")
const allActive = computed(() => activeDirectoryId.value === null);

function goToAll() {
  activeDirectoryId.value = null;
  activeDirName.value = "";
  loadDefs();
}

// ── Breadcrumb path (build from tree) ──
const breadcrumbPath = computed(() => {
  const parts = [];
  if (activeDirectoryId.value) {
    // Find the node and its parent in tree
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
    // Fallback: if tree structure doesn't match (e.g. after refresh), just show name
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
  { title: "操作", dataIndex: "actions", width: "160px", align: "center" },
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
    await deleteDefinition(row.id);
    ElMessage.success("已删除");
    loadDefs();
  } catch (_) {}
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
            <!-- Breadcrumb -->
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
            </el-breadcrumb>
            <span class="case-count">{{ definitions.length }} 个用例</span>
          </div>
          <div class="case-toolbar__right">
            <!-- View toggle -->
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
            <AnimalButton type="primary" @click="create"
              >+ 新建用例</AnimalButton
            >
          </div>
        </div>

        <!-- Content area -->
        <section class="case-content">
          <!-- Card View -->
          <div v-if="viewMode === 'card'" class="card-grid">
            <CaseCard
              v-for="item in definitions"
              :key="item.id"
              :item="item"
              @edit="edit"
              @delete="remove"
            />
          </div>

          <!-- List View -->
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
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.case-layout {
  display: flex;
  gap: 0;
  padding: 0;
  max-width: 1320px;
  margin: 0 auto;
}

.case-sidebar {
  width: 260px;
  flex-shrink: 0;
  min-height: calc(100vh - 200px);
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

/* ── Content ── */
.case-content {
  flex: 1;
}

/* Card Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
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
</style>
