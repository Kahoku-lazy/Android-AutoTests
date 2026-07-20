<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElTag } from 'element-plus'
import ConfirmButton from '@/shared/components/patterns/ConfirmButton.vue'
// Card/AppTable → AppCard/AppTable
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import DirectoryTree from "./components/DirectoryTree.vue";
import CaseAppCard from "./components/CaseCard.vue";
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
// ── Auto-refresh timer for data sync
let refreshTimer = null;

onMounted(async () => {
  window.addEventListener("mousemove", onSidebarResizeMove);
  window.addEventListener("mouseup", onSidebarResizeEnd);
  await loadDirectories();
  await loadDefs();
  refreshTimer = setInterval(loadDefs, 30000);  // 30s auto-refresh
});

onUnmounted(() => {
  clearInterval(refreshTimer);
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

// ── AppTable columns ──
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

async function doRemove(row) {
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
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="测试用例"
      subtitle="管理自动化测试用例工程，支持目录层级、分类与双视图浏览"
      mark="📋"
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
            <el-button class="wb-btn"
              type="primary"
              :loading="exportLoading"
              @click="doExportYaml"
              >📤 导出 YAML</el-button>
            <el-button class="wb-btn" type="primary" @click="create"
              >+ 新建用例</el-button>
          </div>
        </div>

        <!-- === Detail View === -->
        <div v-if="selectedCase" class="case-detail">
          <div class="case-detail__toolbar">
            <el-button class="wb-btn" size="small" @click="handleBackToList"
              >↩ 返回列表</el-button>
            <el-button class="wb-btn"
              size="small"
              type="primary"
              @click="edit(selectedCase)"
              >📝 编辑用例</el-button>
          </div>

          <AppCard color="app-teal" pattern="app-teal" class="case-detail__header">
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
          </AppCard>

          <div class="case-detail__steps">
            <h3 class="case-detail__steps-title">
              📋 测试步骤 ({{ (selectedCase.steps_data || []).length }})
            </h3>
            <AppCard color="brown" pattern="brown">
              <StepViewer :steps="selectedCase.steps_data || []" />
            </AppCard>
          </div>
        </div>

        <!-- === List View === -->
        <div v-else class="case-content">
          <!-- AppCard Grid -->
          <div v-if="viewMode === 'card'" class="card-grid">
            <template v-if="definitions.length > 0">
              <CaseAppCard
                v-for="item in definitions"
                :key="item.id"
                :item="item"
                @edit="edit"
                @delete="(item) => doRemove(item)"
                @select="loadCaseDetail(item.id)"
                @refresh="loadDefinitions"
              />
            </template>
            <div v-else class="card-grid-empty">
              <span>📋</span>
              <p>{{ allActive ? "暂无用例定义" : "此目录下暂无用例" }}</p>
              <el-button class="wb-btn" size="small" type="primary" @click="create">创建第一个用例</el-button>
            </div>
          </div>

          <!-- AppTable -->
          <AppCard v-else color="brown" pattern="brown" class="table-card">
            <AppTable
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
                  <ConfirmButton
                    class="act-btn act-btn--del"
                    :message="`删除用例「${record.title}」？`"
                    title="确认删除"
                    confirm-text="删除"
                    @confirm="doRemove(record)"
                  >删除</ConfirmButton>
                </div>
              </template>
              <template #empty>
                <div class="table-empty">
                  <span>📋</span>
                  <p>{{ allActive ? "暂无用例定义" : "此目录下暂无用例" }}</p>
                  <el-button class="wb-btn" size="small" type="primary" @click="create"
                    >创建第一个用例</el-button>
                </div>
              </template>
            </AppTable>
          </AppCard>
        </div>

        <!-- YAML Export file list -->
        <div v-if="showExports" class="case-exports">
          <div class="case-exports__header">
            <h3 class="case-exports__title">📤 导出文件</h3>
            <el-button class="wb-btn" size="small" @click="showExports = false"
              >✕ 收起</el-button>
          </div>
          <AppCard color="brown" pattern="brown" class="case-exports__table">
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
                    <el-button class="wb-btn"
                      size="small"
                      type="primary"
                      @click="downloadExportFile(file.name)"
                      >⬇ 下载</el-button>
                  </td>
                </tr>
              </tbody>
            </table>
          </AppCard>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped src="./index.css"></style>
