<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import CaseCard from "../CaseCard.vue";
import StepViewer from "../StepViewer.vue";
import {
  listDefinitions,
  deleteDefinition,
  getDefinition,
  exportYaml,
  listExports,
} from "../../api/uiAutomation.js";

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeDirectoryId: { default: null },
  activeDirName: { type: String, default: "" },
});
const emit = defineEmits(["refresh-tree"]);

const router = useRouter();

const definitions = ref([]);
const loading = ref(false);
const selectedCase = ref(null);
const selectedCaseLoading = ref(false);

// View mode
const STORAGE_KEY = "case-manager-view-mode";
const viewMode = ref(localStorage.getItem(STORAGE_KEY) || "card");
function setViewMode(mode) {
  viewMode.value = mode;
  localStorage.setItem(STORAGE_KEY, mode);
}

// YAML export
const exportLoading = ref(false);
const exportFiles = ref([]);
const showExports = ref(false);

// Auto-refresh
let refreshTimer = null;
onMounted(() => {
  loadDefs();
  refreshTimer = setInterval(loadDefs, 30000);
});
onUnmounted(() => clearInterval(refreshTimer));

async function loadDefs() {
  loading.value = true;
  try {
    const { data } = await listDefinitions(props.activeDirectoryId);
    if (data.ok) definitions.value = data.definitions;
  } catch (_) {}
  loading.value = false;
}

// Breadcrumb
const allActive = computed(() => props.activeDirectoryId === null);
const breadcrumbPath = computed(() => {
  if (!props.activeDirectoryId) return [];
  const parts = [];
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
  for (const root of props.treeData) {
    const found = find(root, props.activeDirectoryId);
    if (found) { parts.push(...found); break; }
  }
  if (parts.length === 0 && props.activeDirName) {
    parts.push({ id: props.activeDirectoryId, name: props.activeDirName, parent_id: 1 });
  }
  return parts;
});

// Table columns
const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 220 },
  { title: "目录", dataIndex: "directory_name", minWidth: 160 },
  { title: "分类", dataIndex: "category", minWidth: 120 },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

// Case detail
async function loadCaseDetail(caseId) {
  selectedCaseLoading.value = true;
  try {
    const { data } = await getDefinition(caseId);
    if (data.ok) selectedCase.value = data.definition;
  } catch (_) {}
  selectedCaseLoading.value = false;
}

function goToAll() { emit("refresh-tree"); loadDefs(); }

// Actions
function createCase() {
  const query = props.activeDirectoryId ? { directory_id: props.activeDirectoryId } : {};
  router.push({ path: "/cases/new", query });
}
function editCase(row) { router.push(`/cases/${row.id}/edit`); }
async function doRemove(row) {
  try {
    await deleteDefinition(row.id);
    ElMessage.success("已删除");
    loadDefs();
    emit("refresh-tree");
    if (selectedCase.value?.id === row.id) selectedCase.value = null;
  } catch (e) {
    ElMessage.error("删除失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
  }
}
async function doExportYaml() {
  exportLoading.value = true;
  try {
    const { data } = await exportYaml();
    if (data.ok) {
      ElMessage.success(`YAML 已导出：${data.filename}`);
      const exp = await listExports();
      if (exp.data.ok) exportFiles.value = exp.data.files;
      showExports.value = true;
    }
  } catch (_) {
    ElMessage.error("导出失败");
  }
  exportLoading.value = false;
}

defineExpose({ loadDefs, definitions });
</script>

<template>
  <div class="case-toolbar">
    <div class="case-toolbar__left">
      <nav class="case-breadcrumb">
        <button class="crumb crumb--root" :class="{ 'crumb--active': allActive && !selectedCase }" @click="goToAll">
          <span class="crumb__icon">📋</span>
          <span class="crumb__label">全部用例</span>
        </button>
        <template v-for="node in breadcrumbPath" :key="node.id">
          <span class="crumb-sep">›</span>
          <span class="crumb crumb--active crumb--dir">
            <span class="crumb__icon">{{ node.parent_id === null ? "📁" : "📂" }}</span>
            <span class="crumb__label">{{ node.name }}</span>
          </span>
        </template>
        <template v-if="selectedCase">
          <span class="crumb-sep">›</span>
          <span class="crumb crumb--active crumb--case">
            <span class="crumb__icon">📄</span>
            <span class="crumb__label">{{ selectedCase.title || "未命名用例" }}</span>
          </span>
        </template>
      </nav>
      <span class="case-count-badge">{{ definitions.length }} 个用例</span>
    </div>
    <div class="case-toolbar__right">
      <div class="view-toggle">
        <button :class="{ active: viewMode === 'card' }" @click="setViewMode('card')" title="卡片视图">▦</button>
        <button :class="{ active: viewMode === 'list' }" @click="setViewMode('list')" title="列表视图">☰</button>
      </div>
      <button class="btn-minor" @click="doExportYaml" :disabled="exportLoading">⬇ 导出 YAML</button>
      <button class="btn-primary" @click="createCase">+ 新建用例</button>
    </div>
  </div>

  <!-- Detail view -->
  <div v-if="selectedCase" class="case-detail">
    <div class="case-detail__toolbar">
      <button class="btn-text" @click="selectedCase = null">↩ 返回列表</button>
      <button class="btn-primary" @click="editCase(selectedCase)">📝 编辑用例</button>
    </div>
    <AppCard class="case-detail__card">
      <div class="case-detail__header">
        <span class="case-detail__id">{{ selectedCase.id }}</span>
        <el-tag v-if="selectedCase.enabled" size="small" type="success">启用</el-tag>
        <el-tag v-else size="small" type="info">禁用</el-tag>
        <span class="case-detail__priority">{{ selectedCase.priority }}</span>
        <h2 class="case-detail__title">{{ selectedCase.title }}</h2>
      </div>
      <div class="case-detail__meta">
        <span v-if="selectedCase.category">分类：{{ selectedCase.category }}</span>
        <span v-if="selectedCase.directory_name">目录：{{ selectedCase.directory_name }}</span>
        <span v-if="selectedCase.package_name">包名：{{ selectedCase.package_name }}</span>
        <span>创建者：{{ selectedCase.created_by || '-' }}</span>
      </div>
      <p v-if="selectedCase.description" class="case-detail__desc">{{ selectedCase.description }}</p>
      <StepViewer v-if="selectedCase.steps_data?.length" :steps="selectedCase.steps_data" />
      <p v-else class="case-detail__empty">暂无步骤</p>
    </AppCard>
  </div>

  <!-- List / Card view -->
  <div v-else>
    <div v-if="loading" class="case-loading">加载中...</div>
    <div v-else-if="viewMode === 'card'" class="card-grid">
      <CaseCard
        v-for="item in definitions" :key="item.id"
        :item="item" case-type="ui_automation"
        @edit="editCase(item)" @delete="doRemove(item)"
        @select="loadCaseDetail(item.id)" @refresh="loadDefs(); emit('refresh-tree')"
      />
    </div>
    <AppCard v-else>
      <AppTable :columns="columns" :data-source="definitions" row-key="id" :striped="true" :loading="loading" empty-text="暂无 UI 自动化用例">
        <template #cell-id="{ value }"><code>{{ value }}</code></template>
        <template #cell-title="{ record }">
          <a class="case-link" @click="loadCaseDetail(record.id)">{{ record.title }}</a>
        </template>
        <template #cell-enabled="{ value }">
          <el-tag :type="value ? 'success' : 'info'" size="small">{{ value ? '启用' : '禁用' }}</el-tag>
        </template>
        <template #cell-actions="{ record }">
          <button class="btn-text" @click="loadCaseDetail(record.id)">查看</button>
          <button class="btn-text" @click="editCase(record)">编辑</button>
          <ConfirmButton size="small" type="danger" plain @confirm="doRemove(record)">删除</ConfirmButton>
        </template>
      </AppTable>
    </AppCard>
  </div>

  <!-- YAML Export panel -->
  <div v-if="showExports" class="case-exports">
    <AppCard>
      <h3>📦 已导出的 YAML 文件</h3>
      <table v-if="exportFiles.length" class="exports-table">
        <thead><tr><th>文件名</th><th>大小</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="f in exportFiles" :key="f.name">
            <td>{{ f.name }}</td>
            <td>{{ (f.size / 1024).toFixed(1) }} KB</td>
            <td>{{ f.time }}</td>
            <td><a :href="'/api/cases/exports/' + f.name" download>下载</a></td>
          </tr>
        </tbody>
      </table>
      <p v-else>暂无导出文件</p>
    </AppCard>
  </div>
</template>

<style scoped>
/* Styles inherited from index.css — move to shared if needed */
.case-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 16px 0; flex-wrap: wrap; gap: 8px; }
.case-toolbar__left { display: flex; align-items: center; gap: 12px; }
.case-toolbar__right { display: flex; align-items: center; gap: 8px; }
.case-breadcrumb { display: flex; align-items: center; gap: 4px; }
.crumb { background: none; border: none; cursor: pointer; padding: 4px 8px; border-radius: 6px; font-size: 13px; }
.crumb--active { font-weight: 600; color: var(--animal-primary-color, #89CFF0); }
.crumb-sep { color: #999; font-size: 14px; }
.case-count-badge { font-size: 12px; color: #999; background: #f0f0f0; padding: 2px 10px; border-radius: 12px; }
.view-toggle { display: flex; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; }
.view-toggle button { border: none; background: #fff; padding: 4px 10px; cursor: pointer; font-size: 14px; }
.view-toggle button.active { background: var(--animal-primary-color, #89CFF0); color: #fff; }
.btn-primary, .btn-minor, .btn-text { padding: 6px 16px; border-radius: 8px; border: 1px solid #e0e0e0; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: var(--animal-primary-color, #89CFF0); color: #fff; border-color: var(--animal-primary-color, #89CFF0); }
/* Detail */
.case-detail { padding: 8px 0; }
.case-detail__toolbar { display: flex; justify-content: space-between; margin-bottom: 16px; }
.case-detail__id { font-family: monospace; font-size: 12px; color: #999; }
.case-detail__title { margin: 8px 0; }
.case-detail__meta { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 12px; }
.case-detail__desc { font-size: 14px; color: #444; margin-bottom: 16px; }
/* Card grid */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.case-link { cursor: pointer; color: var(--animal-primary-color, #89CFF0); }
.case-link:hover { text-decoration: underline; }
/* Exports */
.case-exports { margin-top: 24px; }
.exports-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.exports-table th, .exports-table td { padding: 8px 12px; border-bottom: 1px solid #eee; text-align: left; }
</style>
