<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElTag } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { listApiDefinitions, deleteApiDefinition, getApiDefinition } from "../../api/apiTesting.js";

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeDirectoryId: { default: null },
  activeDirName: { type: String, default: "" },
});
const emit = defineEmits(["refresh-tree"]);

const router = useRouter();
const definitions = ref([]);
const loading = ref(false);
const viewMode = ref(localStorage.getItem("case-manager-view-mode") || "card");

function setViewMode(mode) { viewMode.value = mode; localStorage.setItem("case-manager-view-mode", mode); }

const selectedCase = ref(null);
const selectedCaseLoading = ref(false);

async function loadCaseDetail(caseId) {
  selectedCaseLoading.value = true;
  try {
    const { data } = await getApiDefinition(caseId);
    if (data.ok) selectedCase.value = data.definition;
  } catch (_) {}
  selectedCaseLoading.value = false;
}

let refreshTimer = null;
watch(() => props.activeDirectoryId, () => loadDefs());
onMounted(() => { loadDefs(); refreshTimer = setInterval(loadDefs, 30000); });
onUnmounted(() => clearInterval(refreshTimer));

async function loadDefs() {
  loading.value = true;
  try {
    const { data } = await listApiDefinitions(props.activeDirectoryId);
    if (data.ok) definitions.value = data.definitions;
  } catch (_) {}
  loading.value = false;
}

const breadcrumbPath = computed(() => {
  if (!props.activeDirectoryId) return [];
  const parts = [];
  function find(node, id) {
    if (node.id === id) return [node];
    if (node.children) for (const c of node.children) { const f = find(c, id); if (f) return [node, ...f]; }
    return null;
  }
  for (const root of props.treeData) { const f = find(root, props.activeDirectoryId); if (f) { parts.push(...f); break; } }
  if (parts.length === 0 && props.activeDirName) parts.push({ id: props.activeDirectoryId, name: props.activeDirName, parent_id: 1 });
  return parts;
});

const methodColors = { GET: "success", POST: "primary", PUT: "warning", DELETE: "danger", PATCH: "info" };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "方法", dataIndex: "http_method", minWidth: 86, align: "center" },
  { title: "URL", dataIndex: "url", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 180 },
  { title: "状态码", dataIndex: "expected_status", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function createCase() {
  router.push({ path: "/cases/api/new", query: props.activeDirectoryId ? { directory_id: props.activeDirectoryId } : {} });
}
function editCase(row) { router.push(`/cases/api/${row.id}/edit`); }
async function doRemove(row) {
  try {
    await deleteApiDefinition(row.id);
    ElMessage.success("已删除");
    loadDefs(); emit("refresh-tree");
  } catch (e) {
    ElMessage.error("删除失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
  }
}

function goToAll() { emit("refresh-tree"); loadDefs(); }

defineExpose({ loadDefs, definitions });
</script>

<template>
  <div class="case-toolbar">
    <div class="case-toolbar__left">
      <nav class="case-breadcrumb">
        <button class="crumb crumb--root" :class="{ 'crumb--active': activeDirectoryId === null }" @click="goToAll">
          <span class="crumb__icon">🌐</span><span class="crumb__label">全部 API 用例</span>
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
        <button :class="{ active: viewMode === 'card' }" @click="setViewMode('card')">▦</button>
        <button :class="{ active: viewMode === 'list' }" @click="setViewMode('list')">☰</button>
      </div>
      <button class="btn-primary" @click="createCase">+ 新建 API 用例</button>
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
        <el-tag :type="methodColors[selectedCase.http_method] || 'info'" size="small">{{ selectedCase.http_method }}</el-tag>
        <code class="case-detail__id">{{ selectedCase.id }}</code>
        <el-tag v-if="selectedCase.enabled" size="small" type="success">启用</el-tag>
        <el-tag v-else size="small" type="info">禁用</el-tag>
        <h2 class="case-detail__title">{{ selectedCase.title }}</h2>
      </div>
      <div class="case-detail__meta">
        <span v-if="selectedCase.url">URL：<code>{{ selectedCase.url }}</code></span>
        <span v-if="selectedCase.expected_status">期望状态码：{{ selectedCase.expected_status }}</span>
        <span v-if="selectedCase.directory_name">目录：{{ selectedCase.directory_name }}</span>
        <span>创建者：{{ selectedCase.created_by || '-' }}</span>
      </div>
      <p v-if="selectedCase.description" class="case-detail__desc">{{ selectedCase.description }}</p>
      <div v-if="selectedCase.headers" class="case-detail__code-block">
        <h4>Headers</h4>
        <pre>{{ typeof selectedCase.headers === 'string' ? selectedCase.headers : JSON.stringify(selectedCase.headers, null, 2) }}</pre>
      </div>
      <div v-if="selectedCase.body" class="case-detail__code-block">
        <h4>Body</h4>
        <pre>{{ typeof selectedCase.body === 'string' ? selectedCase.body : JSON.stringify(selectedCase.body, null, 2) }}</pre>
      </div>
      <div v-if="selectedCase.expected_response" class="case-detail__code-block">
        <h4>Expected Response</h4>
        <pre>{{ typeof selectedCase.expected_response === 'string' ? selectedCase.expected_response : JSON.stringify(selectedCase.expected_response, null, 2) }}</pre>
      </div>
    </AppCard>
  </div>

  <!-- List / Card view -->
  <div v-else>
    <div v-if="loading" class="case-loading">加载中...</div>
    <div v-else-if="viewMode === 'card'" class="card-grid">
      <AppCard v-for="item in definitions" :key="item.id" class="api-card" @click="loadCaseDetail(item.id)">
      <div class="api-card__header">
        <el-tag :type="methodColors[item.http_method] || 'info'" size="small">{{ item.http_method }}</el-tag>
        <code class="api-card__url">{{ item.url || '(未设置 URL)' }}</code>
      </div>
      <h3 class="api-card__title">{{ item.title }}</h3>
      <p v-if="item.description" class="api-card__desc">{{ item.description }}</p>
      <div class="api-card__meta">
        <span>期望状态码：{{ item.expected_status }}</span>
        <span v-if="item.directory_name">目录：{{ item.directory_name }}</span>
        <el-tag :type="item.enabled ? 'success' : 'info'" size="small">{{ item.enabled ? '启用' : '禁用' }}</el-tag>
      </div>
      <div class="api-card__actions" @click.stop>
        <button class="btn-text" @click="editCase(item)">编辑</button>
        <ConfirmButton size="small" type="danger" plain @confirm="doRemove(item)">删除</ConfirmButton>
      </div>
    </AppCard>
  </div>
  <AppCard v-else>
    <AppTable :columns="columns" :data-source="definitions" row-key="id" :striped="true" :loading="loading" empty-text="暂无 API 接口用例">
      <template #cell-id="{ value }"><code>{{ value }}</code></template>
      <template #cell-http_method="{ value }">
        <el-tag :type="methodColors[value] || 'info'" size="small">{{ value }}</el-tag>
      </template>
      <template #cell-url="{ value }"><code style="font-size:12px;">{{ value }}</code></template>
      <template #cell-title="{ record }"><span class="case-link" @click="loadCaseDetail(record.id)">{{ record.title }}</span></template>
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
</template>

<style scoped>
.case-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 16px 0; flex-wrap: wrap; gap: 8px; }
.case-toolbar__left { display: flex; align-items: center; gap: 12px; }
.case-toolbar__right { display: flex; align-items: center; gap: 8px; }
.case-breadcrumb { display: flex; align-items: center; gap: 4px; }
.crumb { background: none; border: none; cursor: pointer; padding: 4px 8px; border-radius: 6px; font-size: 13px; }
.crumb--active { font-weight: 600; color: var(--app-green, #89CFF0); }
.crumb-sep { color: #999; font-size: 14px; }
.case-count-badge { font-size: 12px; color: #999; background: #f0f0f0; padding: 2px 10px; border-radius: 12px; }
.view-toggle { display: flex; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; }
.view-toggle button { border: none; background: #fff; padding: 4px 10px; cursor: pointer; font-size: 14px; }
.view-toggle button.active { background: var(--app-green, #89CFF0); color: #fff; }
.btn-primary, .btn-text { padding: 6px 16px; border-radius: 8px; border: 1px solid #e0e0e0; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: var(--app-green, #89CFF0); color: #fff; border-color: var(--app-green, #89CFF0); }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.api-card__header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.api-card__url { font-size: 12px; color: #666; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.api-card__title { margin: 0 0 8px 0; font-size: 16px; }
.api-card__desc { font-size: 13px; color: #666; margin-bottom: 8px; }
.api-card__meta { display: flex; gap: 12px; font-size: 12px; color: #999; margin-bottom: 8px; align-items: center; }
.api-card__actions { display: flex; gap: 8px; }
/* Detail */
.case-detail { padding: 8px 0; }
.case-detail__toolbar { display: flex; justify-content: space-between; margin-bottom: 16px; }
.case-detail__header { margin-bottom: 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.case-detail__id { font-family: monospace; font-size: 12px; color: #999; background: rgba(162,210,255,0.14); padding: 2px 8px; border-radius: 6px; }
.case-detail__title { margin: 8px 0; font-size: 18px; width: 100%; }
.case-detail__meta { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 12px; flex-wrap: wrap; }
.case-detail__desc { font-size: 14px; color: #444; margin-bottom: 16px; }
.case-detail__code-block { margin-top: 12px; }
.case-detail__code-block h4 { font-size: 13px; margin-bottom: 4px; }
.case-detail__code-block pre { background: rgba(162,210,255,0.08); padding: 12px; border-radius: 8px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
.case-link { cursor: pointer; color: var(--app-green, #89CFF0); }
.case-link:hover { text-decoration: underline; }
.case-loading { text-align: center; padding: 48px; color: #999; }
</style>

